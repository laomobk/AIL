package ail

import (
	"fmt"
	"strconv"
	"strings"
	"unicode"
	"unicode/utf8"
)

type Scanner struct {
	source       []byte
	sourceLength int
	fileName     string

	cp int
	ch rune

	isEOF bool

	col, line int

	NowToken *Token
}

func (s *Scanner) syntaxErrorWithMsg(msg string) {
	err := ErrNewRuntimeErrorTM("SyntaxError", msg)
	ErrSetError(err)
}

func (s *Scanner) syntaxErrorNoMsg() {
	s.syntaxErrorWithMsg("")
}

func (s *Scanner) nextNChar(step int) (ch rune) {
	for i := 0; i < step && !s.isEOF; i++ {
		ch = s.nextChar()
	}
	return
}

func (s *Scanner) nextChar() rune {
	if s.cp >= s.sourceLength {
		s.isEOF = true
		return -1
	}
	if s.isEOF {
		return -1
	}

	ch, size := utf8.DecodeRune(s.source[s.cp:])
	s.cp += size

	s.col += 1

	if ch == '\n' {
		s.line += 1
		s.col = 0
	}

	return ch
}

func (s *Scanner) nowChar() rune {
	if s.isEOF {
		return -1
	}

	ch, _ := utf8.DecodeRune(s.source[s.cp:])
	return ch
}

func (s *Scanner) peek() rune {
	if s.isEOF {
		return -1
	}

	_, size := utf8.DecodeRune(s.source[s.cp:])
	if s.cp+size >= s.sourceLength {
		return -1
	}

	ch, _ := utf8.DecodeRune(s.source[s.cp+size:])
	return ch
}

func (s *Scanner) setToken(value string, kind token) {
	s.NowToken = &Token{
		value: value,
		kind:  kind,
		op:    0,
		pos:   Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) parseNumber() error {
	numBuf := new(strings.Builder)
	numPow := new(strings.Builder)
	numBase := 10
	numType := _INTEGER

	fprintf := fmt.Fprintf

	canDot := true
	validChar := "0123456789"
	errMsg := ""

	if s.nowChar() == '0' {
		fprintf(numBuf, "0")
		s.nextChar()

		switch s.nowChar() {

		case 'x':
			validChar = "0123456789abcdefABCDEF"
			numBase = 16
			canDot = false
		case 'o':
			validChar = "01234567"
			numBase = 8
			canDot = false
		case 'b':
			validChar = "01"
			numBase = 2
			canDot = false
		case '.':
			numType = _FLOAT
			canDot = false
		case 'e':
			canDot = false
			validChar = "0123456789."
			numBuf = numPow
		default:
			if !runeInString(s.nowChar(), validChar) {
				goto setToken
			}
		}
		s.nextChar()
	}

	for ch := s.nowChar(); ch != -1; ch = s.nowChar() {
		fprintf(numBuf, string(ch))

		if !runeInString(ch, validChar) {

		}

		if ch == '.' {
			if !canDot {
				return fmt.Errorf("invalid number")
			}
			ch = s.nextChar()
			fprintf(numBuf, ".")
			canDot = false
			continue
		}
	}

	return nil

setToken:
	s.NowToken.value = numBuf.String()
	s.NowToken.kind = _NUMBER
	s.NowToken.numBase = numBase
	s.NowToken.numType = numType

	if val, err := strconv.Atoi(numPow.String()); err == nil {
		s.NowToken.numPower = val
	} else {
		return err
	}

	return nil
}

func (s *Scanner) NextToken() bool {
again:
	if s.isEOF {
		s.NowToken.kind = _EOF
	}

	tokKind := &s.NowToken.kind
	tokOp := &s.NowToken.op
	s.NowToken.pos = Pos{col: s.col, line: s.line}

	if unicode.IsNumber(s.nowChar()) {

	}

	switch s.nowChar() {

	case '(':
		*tokKind = _LPAREN
		goto singleChar
	case '[':
		*tokKind = _LBRACK
		goto singleChar
	case '{':
		*tokKind = _LBRACE
		goto singleChar
	case ')':
		*tokKind = _RPAREN
		goto singleChar
	case ']':
		*tokKind = _RBRACK
		goto singleChar
	case '}':
		*tokKind = _RBRACE
		goto singleChar
	case ',':
		*tokKind = _COMMA
		goto singleChar
	case ';':
		*tokKind = _SEMI
		goto singleChar
	case '.':
		*tokKind = _DOT
		goto singleChar
	case ':':
		*tokKind = _COLON
		goto singleChar
	case '@':
		*tokKind = _AT
		goto singleChar
	case '*':
		*tokOp = _MUIT
		if s.peek() == '*' {
			s.nextNChar(2)
			*tokOp = _POWER
		}
		goto checkAssi
	case '/':
		*tokOp = _DIVI
		s.nextChar()
		if s.nextChar() == '/' {
			s.nextChar()
			s.skipLineComment()
			goto again
		} else if s.nowChar() == '*' {
			s.nextChar()
			s.skipBlockComment()
			goto again
		}
		goto checkAssi
	case '%':
		*tokOp = _MOD
		s.nextChar()
		goto checkAssi
	case '^':
		*tokOp = _XOR
		s.nextChar()
		goto checkAssi
	case '&':
		*tokOp = _BAND
		s.nextChar()
		goto checkAssi
	case '|':
		*tokOp = _BOR
		s.nextChar()
		goto checkAssi
	case '<':
		*tokOp = _LTH
		if s.peek() == '<' {
			s.nextNChar(2)
			*tokOp = _LSHIFT
			goto checkAssi
		} else if s.peek() == '=' {
			s.nextNChar(2)
			*tokOp = _LEQ
			*tokKind = _OPERATOR
			break
		}
	case '>':
		*tokOp = _GTH
		if s.peek() == '>' {
			s.nextNChar(2)
			*tokOp = _RSHIFT
			goto checkAssi
		} else if s.peek() == '=' {
			s.nextNChar(2)
			*tokOp = _GEQ
			*tokKind = _OPERATOR
			break
		}
	case '!':
		s.nextChar()
		if s.nowChar() == '=' {
			s.nextChar()
			*tokOp = _UEQ
			*tokKind = _OPERATOR
			break
		}
	case '+':
		*tokOp = _PLUS
		s.nextChar()
		goto checkAssi
	case '-':
		*tokOp = _SUB
		s.nextChar()
		goto checkAssi
	case '~':
		*tokOp = _BNG
		s.nextChar()
		goto checkAssi
	}

	return true

checkAssi:
	*tokKind = _OPERATOR
	if s.nowChar() == '=' {
		s.nextChar()
		*tokOp += assiInc
	}

	return true

singleChar:
	s.NowToken.value = string(s.nowChar())
	s.nextChar()

	return true
}

func (s *Scanner) skipLineComment() {
	s.nextChar()
	for s.nowChar() != '\n' || s.nowChar() != -1 {
		s.nextChar()
	}
}

func (s *Scanner) skipBlockComment() {
	s.nextChar()
	for s.nowChar() != -1 {
		if s.nextChar() == '*' && s.nextChar() == '/' {
			return
		}
	}
}

func (s *Scanner) GetTokenList() []*Token {
	var tokList []*Token
	for s.nowChar() != -1 {
		s.NextToken()
		tok := s.NowToken
		tokList = append(tokList, tok)
	}
	return tokList
}

func NewScanner(source []byte, fileName string) *Scanner {
	scanner := new(Scanner)
	scanner.source = source
	scanner.sourceLength = len(source)
	scanner.fileName = fileName
	scanner.NowToken = new(Token)

	if len(source) == 0 {
		scanner.isEOF = true
	}

	scanner.col, scanner.line, scanner.cp, scanner.ch = 0, 0, 0, 0

	return scanner
}
