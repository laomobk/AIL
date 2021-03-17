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

func (p *Parser) expect(tok int) bool {
	if p.nowToken().Kind == tok {
		p.nextToken()
		return true
	}
	return false
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
		expr.CellTypeStr = TokGetTokenName(nt.Kind)
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

//
// elif x {...} -> else { if x {...} }
func (p *Parser) _ComposeElifBlockIntoElseBlock(
	elifBlock []*IfStmt, elseBlock *Block) *Block {

	lenBlocks := len(elifBlock)

	if lenBlocks == 0 {
		return elseBlock
	}

	for i := range elifBlock {
		eBlock := elifBlock[lenBlocks-(i+1)]
		elifBlock[lenBlocks-(i+1)] = nil // free

		eBlock.ElseBody = elseBlock
		elseBlock = p._newBlockWithStmt(eBlock)
	}

	return elseBlock
}

func (p *Parser) ParseIfStmt() (*IfStmt, error) {
	if p.nowToken().Kind != TokIf {
		return nil, _Expect(p.Pos(), "'if'")
	}
	pos := p.Pos()

	p.nextToken() // eat 'if'

	ifCond, err := p.ParseExpression()
	if err != nil {
		return nil, err
	}

	ifBody, err := p.ParseBlock()
	if err != nil {
		return nil, err
	}

	elifBlocks := make([]*IfStmt, 0)

	for p.nowToken().Kind == TokElif {
		ePos := p.Pos()

		p.nextToken() // eat 'elif'

		elifCond, err := p.ParseExpression()
		if err != nil {
			return nil, err
		}

		elifBody, err := p.ParseBlock()
		if err != nil {
			return nil, err
		}

		elifBlock := new(IfStmt)
		elifBlock.SetPos(ePos)
		elifBlock.Condition = elifCond
		elifBlock.IfBody = elifBody

		elifBlocks = append(elifBlocks, elifBlock)
	}

	var elseBody *Block

	if p.nowToken().Kind != TokElse {
		goto noElse
	}

	p.nextToken() // eat 'else'

	elseBody, err = p.ParseBlock()
	if err != nil {
		return nil, err
	}

noElse:
	stmt := new(IfStmt)
	stmt.SetPos(pos)
	stmt.Condition = ifCond
	stmt.IfBody = ifBody
	stmt.ElseBody = p._ComposeElifBlockIntoElseBlock(
		elifBlocks, elseBody)

	return stmt, nil
}

func (p *Parser) ParseExprList() ([]Expression, error) {
	exprList := make([]Expression, 0)

	for {
		expr, err := p.ParseExpression()
		if err != nil {
			return nil, err
		}

		exprList = append(exprList, expr)

		if p.nowToken().Kind != TokComma {
			return exprList, nil
		}
		p.nextToken() // eat ','
	}
}

func (p *Parser) ParseForStmt() (*ForStmt, error) {
	if p.nowToken().Kind != TokFor {
		return nil, _Expect(p.Pos(), "'for'")
	}

	pos := p.Pos()

	p.nextToken() // eat 'for'

	var body *Block
	var init []Expression
	var condition Expression
	var update []Expression

	var err error

	if p.nowToken().Kind == TokLbrace { // forever
		_body, err := p.ParseBlock()
		if err != nil {
			return nil, err
		}
		body = _body // I DON'T KNOW HOW TO DEAL WITH IT...
		goto finish
	}

	init, err = p.ParseExprList()
	if err != nil {
		return nil, err
	}

	// check single expression: for expr {...}

	if len(init) == 1 && p.nowToken().Kind == TokLbrace {
		// move expr to condition part
		condition = init[0]
		init = nil
		_body, err := p.ParseBlock()
		if err != nil {
			return nil, err
		}
		body = _body
		goto finish
	}

	// classical for stmt

	if p.nowToken().Kind != TokSemi {
		return nil, _Expect(p.Pos(), "';'")
	}
	p.nextToken()

	if p.nowToken().Kind == TokSemi {
		goto noCondition
	}

	condition, err = p.ParseExpression()
	if err != nil {
		return nil, err
	}

noCondition:
	if p.nowToken().Kind != TokSemi {
		return nil, _Expect(p.Pos(), "';'")
	}

	p.nextToken()

	if p.nowToken().Kind == TokLbrace {
		goto noUpdate
	}

	update, err = p.ParseExprList()
	if err != nil {
		return nil, err
	}

noUpdate:
	body, err = p.ParseBlock()
	if err != nil {
		return nil, err
	}

finish:
	stmt := new(ForStmt)
	stmt.SetPos(pos)
	stmt.Condition = condition
	stmt.InitExprList = init
	stmt.UpdateExprList = update
	stmt.Body = body

	return stmt, nil
}

func (p *Parser) _ParseCatchCases() ([]*CatchCase, error) {
	cases := make([]*CatchCase, 0)

	var err error
	var expr Expression
	var alias string

	for p.nowToken().Kind == TokCatch {
		p.nextToken() // eat 'catch'
		pos := p.Pos()

		if p.nowToken().Kind == TokLbrace {
			goto noExpr
		}

		expr, err = p.ParseExpression()
		if err != nil {
			return nil, err
		}

		if p.nowToken().Kind == TokAs {
			p.nextToken() // eat 'as'
			if p.nowToken().Kind != TokIdentifier {
				return nil, _Expect(p.Pos(), "name")
			}

			alias = p.nowToken().Value

			p.nextToken() // eat name
		}

	noExpr:
		body, err := p.ParseBlock()
		if err != nil {
			return nil, err
		}

		c := new(CatchCase)
		c.SetPos(pos)
		c.CaseExpr = expr
		c.Body = body
		c.Alias = alias

		cases = append(cases, c)

		alias = ""
		expr = nil
		err = nil
	}

	return cases, nil
}

func (p *Parser) ParseTryStmt() (*TryStmt, error) {
	if p.nowToken().Kind != TokTry {
		return nil, _Expect(p.Pos(), "'try'")
	}

	pos := p.Pos()

	var err error

	p.nextToken() // eat 'try'

	var cases []*CatchCase

	body, err := p.ParseBlock()
	if err != nil {
		return nil, err
	}

	if p.nowToken().Kind != TokCatch {
		if p.nowToken().Kind == TokFinally {
			goto noCatch
		} else {
			return nil, _Expect(p.Pos(), "'catch' or 'finally'")
		}
	}

	cases, err = p._ParseCatchCases()
	if err != nil {
		return nil, err
	}

noCatch:
	var finallyBody *Block

	if p.nowToken().Kind != TokFinally {
		goto noFinally
	}

	p.nextToken() // eat 'finally'

	finallyBody, err = p.ParseBlock()
	if err != nil {
		return nil, err
	}

noFinally:
	stmt := new(TryStmt)
	stmt.SetPos(pos)
	stmt.TryBlock = body
	stmt.CatchCases = cases
	stmt.FinallyBlock = finallyBody

	return stmt, nil
}

func (p *Parser) ParseParamList() ([]*Param, error) {
	params := make([]*Param, 0)

	for {
		pos := p.Pos()
		nt := p.nowToken()

		star := tokIsOperator(nt, nt.Op)
		kwStar := tokIsOperator(nt, nt.Op)

		if star || kwStar {
			p.nextToken() // eat '*' or '**'
		}

		if p.nowToken().Kind == TokIdentifier {
			return nil, _Expect(pos, "name")
		}

		name := p.nowToken().Value

		param := new(Param)
		param.SetPos(pos)
		param.Name = name
		param.Star = star
		param.KwStar = kwStar

		params = append(params, param)

		if p.nextToken().Kind != TokComma {
			break
		}

		p.nextToken() // eat ','
	}
}

func (p *Parser) ParseFuncDef() (*FuncDefStmt, error) {
	pos := p.Pos()

	if !p.expect(TokFunc) {
		return nil, _Expect(p.Pos(), "'func'")
	}

	if p.nowToken().Kind != TokIdentifier {
		return nil, _Expect(p.Pos(), "name")
	}

	name := p.nowToken().Value

	p.nextToken()

	if !p.expect(TokLparen) {
		return nil, _Expect(p.Pos(), "'('")
	}

	var params []*Param

	if p.nowToken().Kind != TokRparen {
		param, err := p.ParseParamList()
		if err != nil {
			return nil, err
		}
	}

	if !p.expect(TokRparen) {
		return nil, _Expect(p.Pos(), "')'")
	}

	body, err := p.ParseBlock()
	if err != nil {
		return nil, err
	}

	funcDef := new(FuncDefStmt)
	funcDef.SetPos(pos)
	funcDef.Name = name

	return nil, nil
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
	switch p.nowToken().Kind {

	case TokIf:
		return p.ParseIfStmt()
	case TokFor:
		return p.ParseForStmt()
	case TokTry:
		return p.ParseTryStmt()
	default:
		return p.ParseExprStmt()
	}
}

func (p *Parser) _newBlockWithStmt(s Statement) *Block {
	block := new(Block)
	block.SetPos(p.Pos())
	block.Stmts = []Statement{s}

	return block
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

	if p.nowToken().Kind == TokRbrace {
		p.nextToken() // eat '}'
		goto finish
	}

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

finish:
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
