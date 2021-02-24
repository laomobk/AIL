package internal

import "fmt"

type Parser struct {
	tokList       []Token
	tokListLength int

	source []byte
	tp     int
}

func (p *Parser) nowToken() *Token {
	if p.tp >= p.tokListLength {
		return EOFToken
	}
	return &p.tokList[p.tp]
}

func (p *Parser) nextToken() *Token {
	if p.tp+1 >= p.tokListLength {
		return EOFToken
	}
	p.tp += 1
	return &p.tokList[p.tp]
}

func (p *Parser) Pos() Pos {
	return p.nowToken().Pos
}

func (p *Parser) ParseCell() (Expression, error) {
	expr := new(CellExpr)
	expr.pos = p.Pos()
	nt := p.nowToken()

	switch nt.Kind {

	case TokIdentifier, TokString:
		expr.Value = nt.Value
		expr.Type = nt.Kind
	case TokNumber:
		expr.Value = nt.Value
		expr.Type = TokNumber
		expr.NumFlags = nt.NumTypeFlags
	default:
		return nil, fmt.Errorf("except identifier, number or string")

	}

	return expr, nil
}

func (p *Parser) ParseUnaryExpr() (Expression, error) {
	return p.ParseCell()
}

func (p *Parser) ParseBinaryRHS(left Expression, prec int) (Expression, error) {
	for {
		opTok := p.nowToken()
		nowPrec := GetOpPrec(opTok.Op, opTok.Kind)

		if nowPrec < prec {
			return left, nil
		}

		rhs, err := p.ParseUnaryExpr()
		if err != nil {
			return nil, err
		}

		nextOpTok := p.nowToken()
		nextOpPrec := GetOpPrec(nextOpTok.Op, nextOpTok.Kind)
		if nextOpPrec > prec {
			rhs, err = p.ParseBinaryRHS(rhs, nextOpPrec+1)
			if err != nil {
				return nil, err
			}
		}

		left = &BinaryExpr{
			LHS: left,
			RHS: rhs,
			Op:  opTok.Op,
		}
		left.SetPos(p.Pos())
	}
}

func (p *Parser) ParseBinaryExpr() (Expression, error) {
	left, err := p.ParseUnaryExpr()
	if err != nil {
		return nil, err
	}
	return p.ParseBinaryRHS(left, 0)
}

func NewParser(source []byte, tokList []Token) *Parser {
	p := new(Parser)
	p.source = source
	p.tokList = tokList
	p.tokListLength = len(tokList)

	return p
}
