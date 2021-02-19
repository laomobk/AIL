package internal

import "fmt"

type token = int
type operator = int

type Token struct {
	Value string
	Kind  token
	Op    operator
	Pos   Pos /* a Pos copy */

	NumBase  int
	NumType  int
	NumPower string // valid when NumType == _SCIENCE
}

func (t *Token) String() string {
	if t.Kind == _NUMBER && t.NumType == _SCIENCE {
		return fmt.Sprintf("<token sci number '%s', line: %v, col: %v, e: %s>",
			t.Value, t.Pos.line, t.Pos.col, t.NumPower)
	} else if t.Kind == _NUMBER {
		return fmt.Sprintf("<token number '%s', line: %v, col: %v, base: %v, type: %v>",
			t.Value, t.Pos.line, t.Pos.col, t.NumBase, t.NumType)
	} else if t.Kind == _OPERATOR {
		return fmt.Sprintf("<token operator %s, line: %v, col: %v>",
			getOperatorName(t.Op), t.Pos.line, t.Pos.col)
	} else if t.Kind == _EOF {
		return "<token EOF>"
	}
	return fmt.Sprintf("<token '%s', line: %v, col: %v, type: %s>",
		t.Value, t.Pos.line, t.Pos.col, tokenNames[t.Kind])
}

const (
	_EOF = iota
	_OPERATOR

	_LPAREN
	_LBRACK
	_LBRACE

	_RPAREN
	_RBRACK
	_RBRACE

	_COMMA
	_SEMI
	_DOT
	_COLON
	_AT

	_IDENTIFIER
	_NUMBER
	_STRING
	_DOC_STRING

	_ELSE
	_ELIF
	_IF
	_IMPORT
	_CLASS
	_FUN
	_RETURN
	_TRY
	_CATCH
	_FINALLY
	_BREAK
	_CONTINUE
	_THROW
	_ASSERT
	_FOR
	_PRINT
	_INPUT
	_EXTENDS
)

var keywordStart = _ELSE
var keywordEnd = _EXTENDS

// Operators

const (
	_MUIT = iota
	_DIVI
	_MOD
	_XOR
	_BAND
	_BOR
	_LSHIFT
	_RSHIFT
	_PLUS
	_SUB
	_POWER

	_EQ
	_UEQ
	_GTH
	_LTH
	_GEQ
	_LEQ

	_OR
	_AND

	_BNG // ~
	_NOT

	_ASSIGN

	_ASSI_MUIT
	_ASSI_DIVI
	_ASSI_MOD
	_ASSI_XOR
	_ASSI_BAND
	_ASSI_BOR
	_ASSI_LSHR
	_ASSI_RSHR
	_ASSI_PLUS
	_ASSI_SUB
	_ASSI_POWER
)

var assiInc = 22

// Number
const (
	_FLOAT   = 102 // 0.8f
	_INTEGER = 105 // 3
	_SCIENCE = 108 // 50l
)

// Number bases
const (
	_ORD = 10 // 726
	_HEX = 16 // 0xff
	_OCT = 8  // 0o555
	_BIN = 2  // 0b0101
)

func getTokenName(tok token) string {
	if tok >= 0 && tok < len(tokenNames) {
		return tokenNames[tok]
	}
	return "<INVALID>"
}

var tokenNames []string = []string{
	"_EOF",
	"_OPERATOR",

	"_LPAREN",
	"_LBRACK",
	"_LBRACE",

	"_RPAREN",
	"_RBRACK",
	"_RBRACE",

	"_COMMA",
	"_SEMI",
	"_DOT",
	"_COLON",
	"_AT",

	"_IDENTIFIER",
	"_NUMBER",
	"_STRING",
	"_DOC_STRING",

	"_ELSE",
	"_ELIF",
	"_IF",
	"_IMPORT",
	"_CLASS",
	"_FUN",
	"_RETURN",
	"_TRY",
	"_CATCH",
	"_FINALLY",
	"_BREAK",
	"_CONTINUE",
	"_THROW",
	"_ASSERT",
	"_FOR",
	"_PRINT",
	"_INPUT",
	"_EXTENDS",
}

func getOperatorName(op operator) string {
	if op >= 0 && op < len(operatorNames) {
		return operatorNames[op]
	}
	return "<INVALID>"
}

var operatorNames []string = []string{
	"_MUIT",
	"_DIVI",
	"_MOD",
	"_XOR",
	"_BAND",
	"_BOR",
	"_LSHIFT",
	"_RSHIFT",
	"_PLUS",
	"_SUB",
	"_POWER",

	"_EQ",
	"_UEQ",
	"_GTH",
	"_LTH",
	"_GEQ",
	"_LEQ",

	"_OR",
	"_AND",

	"_BNG", // ~
	"_NOT",

	"_ASSIGN",

	"_ASSI_MUIT",
	"_ASSI_DIVI",
	"_ASSI_MOD",
	"_ASSI_XOR",
	"_ASSI_BAND",
	"_ASSI_BOR",
	"_ASSI_LSHR",
	"_ASSI_RSHR",
	"_ASSI_PLUS",
	"_ASSI_SUB",
	"_ASSI_POWER",
}

var keywordMap map[string]token = map[string]token{
	"if":       _IF,
	"else":     _ELSE,
	"elif":     _ELIF,
	"import":   _IMPORT,
	"class":    _CLASS,
	"return":   _RETURN,
	"try":      _TRY,
	"catch":    _CATCH,
	"finally":  _FINALLY,
	"for":      _FOR,
	"not":      _NOT,
	"and":      _AND,
	"or":       _OR,
	"break":    _BREAK,
	"continue": _CONTINUE,
	"throw":    _THROW,
	"assert":   _ASSERT,
	"print":    _PRINT,
	"input":    _INPUT,
	"extends":  _EXTENDS,
}

func checkAndSetKeyword(tok *Token) {
	if val, ok := keywordMap[tok.Value]; ok {
		tok.Kind = val
	}
}

var opPrecMap map[int]int = map[int]int{
	_ASSIGN:     10,
	_ASSI_MUIT:  10,
	_ASSI_DIVI:  10,
	_ASSI_MOD:   10,
	_ASSI_XOR:   10,
	_ASSI_BAND:  10,
	_ASSI_BOR:   10,
	_ASSI_LSHR:  10,
	_ASSI_RSHR:  10,
	_ASSI_PLUS:  10,
	_ASSI_SUB:   10,
	_ASSI_POWER: 10,
	_OR:         30,
	_AND:        40,
	_BOR:        50,
	_XOR:        60,
	_BAND:       70,
	_EQ:         80,
	_UEQ:        80,
	_LTH:        90,
	_LEQ:        90,
	_GTH:        90,
	_GEQ:        90,
	_LSHIFT:     100,
	_RSHIFT:     100,
	_PLUS:       110,
	_SUB:        110,
	_MUIT:       120,
	_DIVI:       130,
	_MOD:        140,
	_POWER:      150,
}

func getOpPrec(op operator, tok token) int {
	find := -1

	switch tok {

	case _OPERATOR:
		find = op

	default:
		return -1

	}

	v, ok := opPrecMap[find]
	if !ok {
		return -1
	}

	return v
}
