package internal

import (
	"fmt"
	goDebug "runtime/debug"
)

type Parser struct {
	tokList       []Token
	tokListLength int

	source []byte
	tp     int
}

const debug = true

func _SyntaxErrorf(pos Pos, format string, a ...string) error {
	if debug {
		goDebug.PrintStack()
	}
	var msg string

	if format == "" {
		format = "invalid syntax"
	}

	if len(a) == 0 {
		msg = format
	} else {
		msg = fmt.Sprintf(format, a)
	}
	return &SyntaxError{
		ErrMsg: msg,
		Pos:    pos,
	}
}

func _Expect(pos Pos, expected string) error {
	if debug {
		goDebug.PrintStack()
	}
	return &SyntaxError{
		ErrMsg:    fmt.Sprintf("expect %v\n", expected),
		Pos:       pos,
		expecting: true,
	}
}

func (p *Parser) nowToken() *Token {
	if p.tp >= p.tokListLength {
		return EOFToken
	}
	return &p.tokList[p.tp]
}

func (p *Parser) nextToken() *Token {
	p.tp += 1
	if p.tp >= p.tokListLength {
		return EOFToken
	}
	return &p.tokList[p.tp]
}

func (p *Parser) checkArgList(args []*Argument) error {
	canVar := true

	for _, arg := range args {
		if arg.Star {
			if !canVar {
				return _SyntaxErrorf(
					p.Pos(),
					"iterable argument unpacking follows keyword "+
						"argument unpacking")
			}
		} else if arg.KwStar {
			canVar = false
		}
	}
	return nil
}

func (p *Parser) Pos() Pos {
	return p.nowToken().Pos
}

func (p *Parser) ParseCell() (Expression, error) {
	expr := new(CellExpr)
	expr.pos = p.Pos()
	nt := p.nowToken()

	switch nt.Kind {

	case TokIdentifier, TokString, TokNumber:
		expr.Token = p.nowToken()
	case TokLparen:
		p.nextToken() // eat '('
		e, err := p.ParseBinaryExpr()
		if err != nil {
			return nil, err
		}
		if p.nowToken().Kind != TokRparen {
			return nil, _Expect(p.Pos(), "')'")
		}
		p.nextToken() // eat ')'
		return e, nil
	default:
		return nil, _Expect(p.Pos(), "identifier, number or string")

	}

	p.nextToken()

	return expr, nil
}

func (p *Parser) ParseArgList() ([]*Argument, error) {
	var args []*Argument

	for {
		tPos := p.Pos()
		isKw := tokIsOperator(p.nowToken(), OpPower)
		isVarArg := tokIsOperator(p.nowToken(), OpMult)

		if isKw || isVarArg {
			p.nextToken() // eat '*' or '**'
		}

		expr, err := p.ParseExpression()
		if err != nil {
			return nil, err
		}

		arg := new(Argument)
		arg.SetPos(tPos)
		arg.KwStar = isKw
		arg.Star = isVarArg
		arg.Expr = expr

		args = append(args, arg)

		if p.nowToken().Kind != TokComma {
			break
		}
		p.nextToken() // eat ','
	}

	err := p.checkArgList(args)
	if err != nil {
		return nil, err
	}
	return args, nil
}

func (p *Parser) ParseSubscrAccessCallExpr() (Expression, error) {
	var left Expression

	left, err := p.ParseCell()
	for {
		if err != nil {
			return nil, err
		}

		pos := p.Pos()

		switch p.nowToken().Kind {

		case TokLparen: // call
			p.nextToken() // eat '('

			argList := make([]*Argument, 0)
			if p.nowToken().Kind == TokRparen {
				goto noArg
			}

			argList, err = p.ParseArgList()
			if err != nil {
				return nil, err
			}
			if p.nowToken().Kind != TokRparen {
				return nil, _Expect(p.Pos(), "')'")
			}
		noArg:
			p.nextToken() // eat ')'

			callExpr := new(CallExpr)
			callExpr.Arguments = argList
			callExpr.SetPos(pos)
			callExpr.Left = left

			left = callExpr
		case TokLbracket: // subscript
			p.nextToken() // eat '['

			if p.nowToken().Kind == TokRbracket {
				return nil, _Expect(p.Pos(), "expression")
			}

			subScr, err := p.ParseExpression()
			if err != nil {
				return nil, err
			}

			if p.nowToken().Kind != TokRbracket {
				return nil, _Expect(p.Pos(), "']'")
			}

			p.nextToken() // eat ']'

			subScrExpr := new(SubScriptExpr)
			subScrExpr.SetPos(pos)
			subScrExpr.Right = subScr
			subScrExpr.Left = left

			left = subScrExpr
		case TokDot:
			p.nextToken() // eat '.'
			names := make([]string, 0)
			for p.nowToken().Kind == TokIdentifier {
				names = append(names, p.nowToken().Value)
				p.nextToken() // eat NAME

				if p.nowToken().Kind != TokDot {
					break
				}
				p.nextToken() // eat '.'
			}
			accExpr := new(AccessExpr)
			accExpr.Names = names
			accExpr.Left = left
			accExpr.SetPos(pos)

			left = accExpr
		default:
			return left, nil
		}
	}
}

func (p *Parser) ParseUnaryExpr() (Expression, error) {
	if p.nowToken().Kind != TokOperator {
		return p.ParseSubscrAccessCallExpr()
	}

	expr := new(UnaryExpr)
	expr.SetPos(p.Pos())

	switch p.nowToken().Op {

	case OpPlus, OpSub, OpNot:
		expr.Op = p.nowToken().Op
	default:
		return nil, _SyntaxErrorf(p.Pos(), "")

	}

	p.nextToken() // eat op

	rhs, err := p.ParseCell()
	if err != nil {
		return nil, err
	}

	expr.Expr = rhs

	return expr, nil
}

func (p *Parser) ParseBinaryRHS(left Expression, prec int) (Expression, error) {
	for {
		opTok := p.nowToken()
		nowPrec := GetOpPrec(opTok.Op, opTok.Kind)

		if nowPrec < prec {
			return left, nil
		}

		p.nextToken() // eat op

		rhs, err := p.ParseTernaryExpr()
		if err != nil {
			return nil, err
		}

		nextOpTok := p.nowToken()
		nextOpPrec := GetOpPrec(nextOpTok.Op, nextOpTok.Kind)
		if nextOpPrec >= prec {
			rhs, err = p.ParseBinaryRHS(rhs, nextOpPrec+1)
			if err != nil {
				return nil, err
			}
		}

		left = &BinaryExpr{
			LHS:   left,
			RHS:   rhs,
			Op:    opTok.Op,
			OpStr: GetOperatorName(opTok.Op),
		}
		left.SetPos(p.Pos())
	}
}

func (p *Parser) ParseTernaryExpr() (Expression, error) {
	expr, err := p.ParseUnaryExpr()

	if err != nil {
		return nil, err
	}

	pos := p.Pos()

	if p.nowToken().Kind != TokIf {
		return expr, nil
	}

	p.nextToken() // eat 'if'
	ifPart, err := p.ParseExpression()
	if err != nil {
		return nil, err
	}

	if p.nowToken().Kind != TokElse {
		return nil, _Expect(p.Pos(), "'else'")
	}
	p.nextToken() // eat 'else'

	elsePart, err := p.ParseExpression()
	if err != nil {
		return nil, err
	}

	tExpr := new(TernaryExpr)
	tExpr.SetPos(pos)
	tExpr.A = expr
	tExpr.B = elsePart
	tExpr.Condition = ifPart

	return tExpr, nil
}

func (p *Parser) ParseBinaryExpr() (Expression, error) {
	left, err := p.ParseTernaryExpr()
	if err != nil {
		return nil, err
	}
	return p.ParseBinaryRHS(left, OpAssignPrec)
}

func (p *Parser) ParseExpression() (Expression, error) {
	return p.ParseBinaryExpr()
}

func (p *Parser) ParseExprStmt() (*ExprStmt, error) {
	pos := p.Pos()

	expr, err := p.ParseExpression()
	if err != nil {
		return nil, err
	}
	if p.nowToken().Kind != TokSemi {
		return nil, _Expect(p.Pos(), "';'")
	}
	p.nextToken() // eat ';'

	exprStmt := new(ExprStmt)
	exprStmt.SetPos(pos)
	exprStmt.Expr = expr

	return exprStmt, nil
}

func (p *Parser) ParseStmt() (Statement, error) {
	return p.ParseExprStmt()
}

func (p *Parser) parseBlock(forFile bool) (*Block, error) {
	if p.nowToken().Kind != TokLbrace && !forFile {
		return nil, _Expect(p.Pos(), "'{'")
	}

	pos := p.Pos()

	if !forFile {
		p.nextToken() // eat '{'
	}

	stmts := make([]Statement, 0)

	for p.nowToken().Kind != TokRbrace {
		if p.nowToken() == EOFToken {
			if forFile {
				break
			}

			return nil, _Expect(p.Pos(), "'}'")
		}
		stmt, err := p.ParseStmt()
		if err != nil {
			return nil, err
		}
		stmts = append(stmts, stmt)
	}
	if !forFile {
		p.nextToken() // eat '}'
	}

	block := new(Block)
	block.SetPos(pos)
	block.Stmts = stmts

	return block, nil
}

func (p *Parser) ParseBlock() (*Block, error) {
	return p.parseBlock(false)
}

func (p *Parser) Parse() (*Block, error) {
	return p.parseBlock(true)
}

func (p *Parser) ParseWithSource(source []byte, tokList []Token) (Node, error) {
	parser := new(Parser)
	parser.source = source
	parser.tokList = tokList
	parser.tokListLength = len(tokList)

	return parser.Parse()
}

func NewParserWithSource(source []byte, tokList []Token) *Parser {
	p := new(Parser)
	p.source = source
	p.tokList = tokList
	p.tokListLength = len(tokList)

	return p
}
