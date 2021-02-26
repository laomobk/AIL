package internal

import "fmt"

type token = int
type operator = int

type Token struct {
	Value string
	Kind  token
	Op    operator
	Pos   Pos /* a Pos copy */

	NumBase      int
	NumTypeFlags int
	NumPower     string // valid when NumTypeFlags == NumScience
}

var EOFToken = new(Token)

func (t *Token) String() string {
	if t.Kind == TokNumber && t.NumTypeFlags&NumScience != 0 {
		return fmt.Sprintf("<Token sci number '%s', line: %v, col: %v, e: %s>",
			t.Value, t.Pos.line, t.Pos.col, t.NumPower)
	} else if t.Kind == TokNumber {
		return fmt.Sprintf("<Token number '%s', line: %v, col: %v, base: %v, type: %v>",
			t.Value, t.Pos.line, t.Pos.col, t.NumBase, t.NumTypeFlags)
	} else if t.Kind == TokOperator {
		return fmt.Sprintf("<Token operator %s, line: %v, col: %v>",
			GetOperatorName(t.Op), t.Pos.line, t.Pos.col)
	} else if t.Kind == TokEOF {
		return "<Token EOF>"
	}
	return fmt.Sprintf("<Token '%s', line: %v, col: %v, type: %s>",
		t.Value, t.Pos.line, t.Pos.col, TokenNames[t.Kind])
}

const (
	TokEOF = iota
	TokOperator

	TokLparen
	TokLbracket
	TokLbrace

	TokRparen
	TokRbracket
	TokRbrace

	TokComma
	TokSemi
	TokDot
	TokColon
	TokAt

	TokIdentifier
	TokNumber
	TokString
	TokDocString

	TokElse
	TokElif
	TokIf
	TokImport
	TokClass
	TokFun
	TokReturn
	TokTry
	TokCatch
	TokFinally
	TokBreak
	TokContinue
	TokThrow
	TokAssert
	TokFor
	TokPrint
	TokInput
	TokExtends
)

var KeywordStart = TokElse
var KeywordEnd = TokExtends

// Operators

const (
	OpMult = iota
	OpDivi
	OpMod
	OpXor
	OpBand
	OpBor
	OpLshift
	OpRshift
	OpPlus
	OpSub
	OpPower

	OpEq
	OpUeq
	OpGth
	OpLth
	OpGeq
	OpLeq

	OpOr
	OpAnd

	OpBng // ~
	OpNot

	OpAssign

	OpAssiMult
	OpAssiDivi
	OpAssiMod
	OpAssiXor
	OpAssiBand
	OpAssiBor
	OpAssiLshift
	OpAssiRshift
	OpAssiPlus
	OpAssiSub
	OpAssiPower
)

var AssiInc = 22

// NumberType Flags
const (
	NumFloat   = 1 // 0.8f
	NumInteger = 2 // 3
	NumScience = 4 // 50l
)

func tokIsOperator(tok *Token, op operator) bool {
	return tok.Kind == TokOperator && tok.Op == op
}

func TokGetTokenName(tok token) string {
	if tok >= 0 && tok < len(TokenNames) {
		return TokenNames[tok]
	}
	return "<INVALID>"
}

var TokenNames = []string{
	"TokEOF",
	"TokOperator",

	"TokLparen",
	"TokLbracket",
	"TokLbrace",

	"TokRparen",
	"TokRbracket",
	"TokRbrace",

	"TokComma",
	"TokSemi",
	"TokDot",
	"TokColon",
	"TokAt",

	"TokIdentifier",
	"TokNumber",
	"TokString",
	"TokDocString",

	"TokElse",
	"TokElif",
	"TokIf",
	"TokImport",
	"TokClass",
	"TokFun",
	"TokReturn",
	"TokTry",
	"TokCatch",
	"TokFinally",
	"TokBreak",
	"TokContinue",
	"TokThrow",
	"TokAssert",
	"TokFor",
	"TokPrint",
	"TokInput",
	"TokExtends",
}

var OpMap = map[string]int{
	"*":   OpMult,
	"/":   OpDivi,
	"%":   OpMod,
	"^":   OpXor,
	"&":   OpBand,
	"|":   OpBor,
	"<<":  OpLshift,
	">>":  OpRshift,
	"+":   OpPlus,
	"-":   OpSub,
	"**":  OpPower,
	"==":  OpEq,
	"!=":  OpUeq,
	">":   OpGth,
	"<":   OpLth,
	">=":  OpGeq,
	"<=":  OpLeq,
	"~":   OpBng,
	"not": OpNot,
	"and": OpAnd,
	"or":  OpOr,
	"=":   OpAssign,
	"*=":  OpAssiMult,
	"/=":  OpAssiDivi,
	"%=":  OpAssiMod,
	"^=":  OpAssiXor,
	"&=":  OpAssiBand,
	"|=":  OpAssiBor,
	"<<=": OpAssiLshift,
	">>=": OpAssiRshift,
	"+=":  OpAssiPlus,
	"-=":  OpAssiSub,
	"**=": OpAssiPower,
}

func GetOperatorName(op operator) string {
	if op >= 0 && op < len(operatorNames) {
		return operatorNames[op]
	}
	return "<INVALID>"
}

var operatorNames []string = []string{
	"OpMult",
	"OpDivi",
	"OpMod",
	"OpXor",
	"OpBand",
	"OpBor",
	"OpLshift",
	"OpRshift",
	"OpPlus",
	"OpSub",
	"OpPower",

	"OpEq",
	"OpUeq",
	"OpGth",
	"OpLth",
	"OpGeq",
	"OpLeq",

	"OpOr",
	"OpAnd",

	"OpBng", // ~
	"OpNot",

	"OpAssign",

	"OpAssiMult",
	"OpAssiDivi",
	"OpAssiMod",
	"OpAssiXor",
	"OpAssiBand",
	"OpAssiBor",
	"OpAssiLshift",
	"OpAssiRshift",
	"OpAssiPlus",
	"OpAssiSub",
	"OpAssiPower",
}

var KeywordMap = map[string]token{
	"if":       TokIf,
	"else":     TokElse,
	"elif":     TokElif,
	"import":   TokImport,
	"class":    TokClass,
	"return":   TokReturn,
	"try":      TokTry,
	"catch":    TokCatch,
	"finally":  TokFinally,
	"for":      TokFor,
	"not":      OpNot,
	"and":      OpAnd,
	"or":       OpOr,
	"break":    TokBreak,
	"continue": TokContinue,
	"throw":    TokThrow,
	"assert":   TokAssert,
	"print":    TokPrint,
	"input":    TokInput,
	"extends":  TokExtends,
}

func CheckAndSetKeyword(tok *Token) {
	if tok.Value == "and" {
		tok.Kind = TokOperator
		tok.Op = OpAnd
		return
	} else if tok.Value == "or" {
		tok.Kind = TokOperator
		tok.Op = OpOr
		return
	} else if tok.Value == "not" {
		tok.Kind = TokOperator
		tok.Op = OpNot
		return
	}

	if val, ok := KeywordMap[tok.Value]; ok {
		tok.Kind = val
	}
}

var OpAssignPrec = 10

var OpPrecMap = map[int]int{
	OpAssign:     10,
	OpAssiMult:   10,
	OpAssiDivi:   10,
	OpAssiMod:    10,
	OpAssiXor:    10,
	OpAssiBand:   10,
	OpAssiBor:    10,
	OpAssiLshift: 10,
	OpAssiRshift: 10,
	OpAssiPlus:   10,
	OpAssiSub:    10,
	OpAssiPower:  10,
	OpOr:         30,
	OpAnd:        40,
	OpBor:        50,
	OpXor:        60,
	OpBand:       70,
	OpEq:         80,
	OpUeq:        80,
	OpLth:        90,
	OpLeq:        90,
	OpGth:        90,
	OpGeq:        90,
	OpLshift:     100,
	OpRshift:     100,
	OpPlus:       110,
	OpSub:        110,
	OpMult:       120,
	OpDivi:       130,
	OpMod:        140,
	OpPower:      150,
}

func GetOpPrec(op operator, tok token) int {
	find := -1

	switch tok {

	case TokOperator:
		find = op

	default:
		return -1

	}

	v, ok := OpPrecMap[find]
	if !ok {
		return -1
	}

	return v
}
