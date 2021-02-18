package core

import (
	"ail/tools"
	"fmt"
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

	col, line int

	nowToken *Token
}

func (s *Scanner) syntaxErrorWithMsg(msg string) {
	err := ErrNewRuntimeErrorTM(
		fmt.Sprintf("SyntaxError: (%v, %v)", s.line, s.col), msg)
	ErrSetError(err)
}

func (s *Scanner) syntaxErrorNoMsg() {
	s.syntaxErrorWithMsg("")
}

func (s *Scanner) error(err error) {
	msg := err.Error()
	errObj := ErrNewRuntimeErrorTMFL(
		"ScannerError", msg, s.fileName, s.line)
	ErrSetError(errObj)
}

func (s *Scanner) nextNChar(step int) (ch rune) {
	for i := 0; i < step && !s.isEOF(); i++ {
		ch = s.nextChar()
	}
	return
}

func (s *Scanner) isEOF() bool {
	return s.cp >= s.sourceLength
}

func (s *Scanner) nextChar() rune {
	if s.isEOF() {
		return -1
	}

	s.col += 1

	ch, size := utf8.DecodeRune(s.source[s.cp:])
	s.cp += size
	ch, _ = utf8.DecodeRune(s.source[s.cp:])

	if ch == '\n' {
		s.line += 1
		s.col = 0
	}

	return ch
}

func (s *Scanner) nowChar() rune {
	if s.isEOF() {
		return -1
	}

	ch, _ := utf8.DecodeRune(s.source[s.cp:])
	return ch
}

func (s *Scanner) peek() rune {
	if s.isEOF() {
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
	s.nowToken = &Token{
		Value: value,
		Kind:  kind,
		Op:    0,
		Pos:   Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) setNumberToken(
	value string, tKind token, base, nKind int, power string) {
	s.nowToken = &Token{
		Value:    value,
		Kind:     tKind,
		NumBase:  base,
		NumType:  nKind,
		NumPower: power,
		Pos:      Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) setOperatorToken(value string, op operator) {
	s.nowToken = &Token{
		Value: value,
		Kind:  _OPERATOR,
		Op:    op,
		Pos:   Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) parseNumber() error {
	numBuf := new(strings.Builder)
	numPow := new(strings.Builder)
	numBase := 10
	numType := _INTEGER
	baseBuf := new(strings.Builder)

	canDot := true
	validChar := "0123456789.eE"

	if s.nowChar() == '0' {
		numBuf.WriteRune('0')
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
			numBuf.WriteRune('.')
		case 'e', 'E':
			canDot = false
			validChar = "0123456789."
			numBuf = numPow
		default:
			if !tools.RuneInString(s.nowChar(), validChar) {
				goto setToken
			}
		}
		s.nextChar()
	}

	for ch := s.nowChar(); ch != -1; ch = s.nextChar() {
		if !tools.RuneInString(ch, validChar) {
			goto setToken
		}
		if ch == '.' {
			if !canDot {
				return fmt.Errorf("invalid number")
			}
			canDot = false
			numBuf.WriteRune(ch)
		} else if ch == 'e' || ch == 'E' {
			baseBuf = numBuf
			numBuf = numPow
			numType = _SCIENCE
			validChar = "-0123456789."
			canDot = false
		} else {
			numBuf.WriteRune(ch)
		}
	}

setToken:
	if numType == _SCIENCE {
		numPow = numBuf
		numBuf = baseBuf
	}
	s.setNumberToken(numBuf.String(), _NUMBER, numBase, numType, numPow.String())
	return nil
}

func (s *Scanner) parseEscape() (ch rune, err error) {
	switch s.nowChar() {

	case '\'':
		ch = '\''
	case '"':
		ch = '"'
	case 'a':
		ch = '\a'
	case 'b':
		ch = '\b'
	case 'f':
		ch = '\f'
	case 'n':
		ch = '\n'
	case 'r':
		ch = '\r'
	case 't':
		ch = '\t'
	case 'v':
		ch = '\v'
	case '\\':
		ch = '\\'
	case '0':
		ch = '0'
	case 'x':
		ch = 'x'
	default:
		return 0, fmt.Errorf("invaild escape character")
	}

	if ch == '0' || ch == 'x' {

	}

	return ch, nil
}

func (s *Scanner) parseString() error {
	start := s.nowChar()
	buf := new(strings.Builder)

	s.nowToken.Pos = Pos{col: s.col, line: s.line}

	for ch := s.nextChar(); ch != -1; ch = s.nextChar() {
		if ch == start {
			s.nextChar()
			break
		}
		buf.WriteRune(ch)
	}

	s.nowToken.Kind = _STRING
	s.nowToken.Value = buf.String()

	return nil
}

func (s *Scanner) parseIdentifier() error {
	buf := new(strings.Builder)

	s.nowToken.Pos = Pos{s.line, s.col}

	for ch := s.nowChar(); tools.IsIdentifier(ch) && ch != -1; ch = s.nextChar() {
		buf.WriteRune(ch)
	}

	if buf.Len() == 0 {
		return fmt.Errorf("invaild identifier")
	}

	s.nowToken.Value = buf.String()
	s.nowToken.Kind = _IDENTIFIER

	return nil
}

func (s *Scanner) NextToken() bool {
again:
	if s.isEOF() {
		s.nowToken = &Token{
			Kind: _EOF,
		}
		return true
	}

	tokKind := &s.nowToken.Kind
	tokOp := &s.nowToken.Op
	s.nowToken.Pos = Pos{col: s.col, line: s.line}

	if tools.IsWhite(s.nowChar()) {
		s.nextChar()
		goto again
	}

	if unicode.IsNumber(s.nowChar()) {
		if err := s.parseNumber(); err != nil {
			s.error(err)
			return false
		}
		return true
	}

	if tools.IsIdentifier(s.nowChar()) {
		if err := s.parseIdentifier(); err != nil {
			s.error(err)
			return false
		}
		return true
	}

	switch s.nowChar() {
	case '\'', '"':
		err := s.parseString()
		if err != nil {
			s.error(err)
			return false
		}
		return true
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
	case '=':
		*tokOp = _ASSIGN
		*tokKind = _OPERATOR
		s.nextChar()
		if s.nowChar() == '=' {
			*tokOp = _EQ
		}
		return true
	default:
		s.syntaxErrorWithMsg(
			fmt.Sprintf("Unknown character: %v", int32(s.nowChar())))
		return false
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
	s.nowToken.Value = string(s.nowChar())
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

func (s *Scanner) NowToken() Token {
	return *s.nowToken
}

func (s *Scanner) GetTokenList() []Token {
	var tokList []Token
	for !s.isEOF() {
		if !s.NextToken() {
			return nil
		}
		tok := s.NowToken()
		tokList = append(tokList, tok)
	}
	return tokList
}

func NewScanner(source []byte, fileName string) *Scanner {
	scanner := new(Scanner)
	scanner.source = source
	scanner.sourceLength = len(source)
	scanner.fileName = fileName
	scanner.nowToken = new(Token)

	scanner.col, scanner.line, scanner.cp, scanner.ch = 1, 1, 0, 0

	return scanner
}
