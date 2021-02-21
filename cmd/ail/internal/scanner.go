package internal

import (
	"ail/tools"
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
		"SyntaxError", msg, s.fileName, s.line)
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

	if ch == '\n' {
		s.line += 1
		s.col = 0
	}

	s.cp += size
	ch, _ = utf8.DecodeRune(s.source[s.cp:])

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
		Value:        value,
		Kind:         tKind,
		NumBase:      base,
		NumTypeFlags: nKind,
		NumPower:     power,
		Pos:          Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) setOperatorToken(value string, op operator) {
	s.nowToken = &Token{
		Value: value,
		Kind:  TokOperator,
		Op:    op,
		Pos:   Pos{col: s.col, line: s.line},
	}
}

func (s *Scanner) getPos() Pos {
	return Pos{s.line, s.col}
}

func (s *Scanner) parseDocString() error {
	s.nextChar() // eat '#'
	buf := new(strings.Builder)

	s.nowToken.Pos = s.getPos()

	for {
		if s.nowChar() == -1 {
			break
		}

		if s.nowChar() == '\n' {
			if _, err := buf.WriteRune(s.nowChar()); err != nil {
				return err
			}
			if s.nextChar() == '#' {
				s.nextChar()
			} else {
				break
			}
		} else {
			_, err := buf.WriteRune(s.nowChar())
			if err != nil {
				return err
			}
			s.nextChar()
		}
	}

	s.nowToken.Kind = TokString
	s.nowToken.Value = buf.String()
	return nil
}

func (s *Scanner) parseNumber() error {
	numBuf := new(strings.Builder)
	numPow := new(strings.Builder)
	numBase := 10
	numTypeFlags := NumInteger
	baseBuf := new(strings.Builder)

	canDot := true
	canNg := false
	validChar := "0123456789.eE"

	if s.nowChar() == '0' {
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
			numTypeFlags ^= NumFloat | NumInteger
			canDot = false
			numBuf.WriteRune('0')
			numBuf.WriteRune('.')
		case 'e', 'E':
			canDot = false
			validChar = "0123456789."
			numBuf = numPow
		default:
			numBuf.WriteRune('0')
			if !tools.RuneInString(s.nowChar(), validChar) {
				goto setToken
			}
		}
		s.nextChar()
	}

	for ch := s.nowChar(); ch != -1; ch = s.nowChar() {
		if !tools.RuneInString(ch, validChar) {
			goto setToken
		}

		if ch == '-' {
			if numTypeFlags&NumScience != 0 && canNg {
				canNg = false
			}
			if !canNg {
				return fmt.Errorf("invalid number")
			}
		}

		if ch == '.' {
			if !canDot {
				return fmt.Errorf("invalid number")
			}
			canDot = false
			numBuf.WriteRune(ch)
			numTypeFlags ^= NumFloat | NumInteger
		} else if (ch == 'e' || ch == 'E') && numBase != 16 {
			if numBase != 10 {
				return fmt.Errorf("invalid number")
			}
			baseBuf = numBuf
			numBuf = numPow
			numTypeFlags ^= NumScience | NumInteger
			validChar = "-0123456789"
			canDot = false
		} else {
			numBuf.WriteRune(ch)
		}
		s.nextChar()
	}

setToken:
	if numTypeFlags&NumScience != 0 {
		numPow = numBuf
		numBuf = baseBuf
	}
	s.setNumberToken(numBuf.String(), TokNumber, numBase, numTypeFlags, numPow.String())
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
	case '0', '1', '2', '3', '4', '5', '6', '7', '8', '9':
		return s.parseOctEscape()
	case 'x':
		return s.parseHexEscape()
	case 'u':
		return s.parseUnicodeEscape(4)
	case 'U':
		return s.parseUnicodeEscape(8)
	default:
		return 0, fmt.Errorf("invaild escape character")
	}

	return ch, nil
}

func (s *Scanner) parseOctEscape() (rune, error) {
	buf := new(strings.Builder)
	c := 0

	for ch := s.nowChar(); c < 3; c++ {
		if unicode.IsNumber(ch) {
			buf.WriteRune(ch)
		} else {
			break
		}
		ch = s.nextChar()
	}
	tools.Assert(buf.Len() > 0, "'buf' cannot be empty")

	num, err := strconv.ParseInt(buf.String(), 8, 32)
	if err != nil {
		return 0, err
	}
	return rune(num), nil
}

func (s *Scanner) parseHexEscape() (rune, error) {
	buf := new(strings.Builder)
	c := 0

	tools.Assert(
		s.nowChar() == 'x', "char != 'x' when parsing hex escape character")
	s.nextChar() // eat 'x'

	for ch := s.nowChar(); c < 2; c++ {
		buf.WriteRune(ch)
		ch = s.nextChar()
	}

	tools.Assert(buf.Len() > 0, "'buf' cannot be empty")
	num, err := strconv.ParseInt(buf.String(), 16, 32)
	if err != nil {
		return 0, fmt.Errorf(
			"unicode escape cannot decode the position at (line: %v, col: %v)",
			s.line, s.col)
	}
	return rune(num), nil
}

func (s *Scanner) parseUnicodeEscape(length int) (rune, error) {
	buf := new(strings.Builder)
	c := 0

	tools.Assert(
		s.nowChar() == 'u' || s.nowChar() == 'U',
		"char != 'u' or 'U' when parsing hex escape character")
	s.nextChar() // eat 'u' or 'U'

	for ch := s.nowChar(); c < length; c++ {
		buf.WriteRune(ch)
		ch = s.nextChar()
	}

	uNum, err := strconv.ParseInt(buf.String(), 16, 32)
	if err != nil {
		return 0, fmt.Errorf(
			"unicode escape cannot decode the position at (line: %v, col: %v)",
			s.line, s.col)
	}

	return rune(uNum), err
}

func (s *Scanner) parseString() error {
	start := s.nowChar()
	buf := new(strings.Builder)

	s.nowToken.Pos = Pos{col: s.col, line: s.line}

	for ch := s.nextChar(); ; ch = s.nowChar() {
		if ch == start {
			s.nextChar()
			break
		}
		if ch == -1 {
			return fmt.Errorf("EOF while scanning a string literal")
		}
		if ch == '\\' {
			s.nextChar()
			esc, err := s.parseEscape()
			if err != nil {
				return err
			}
			ch = esc
		}
		buf.WriteRune(ch)
		s.nextChar()
	}

	s.nowToken.Kind = TokString
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
		return fmt.Errorf("invaild TokIdentifier")
	}

	s.nowToken.Value = buf.String()
	s.nowToken.Kind = TokIdentifier

	return nil
}

func (s *Scanner) NextToken() error {
again:
	if s.isEOF() {
		s.nowToken = &Token{
			Kind: TokEOF,
		}
		return nil
	}

	tokKind := &s.nowToken.Kind
	tokOp := &s.nowToken.Op
	s.nowToken.Pos = Pos{col: s.col, line: s.line}

	if tools.IsWhite(s.nowChar()) {
		s.nextChar()
		goto again
	}

	if unicode.IsNumber(s.nowChar()) {
		return s.parseNumber()
	}

	if tools.IsIdentifier(s.nowChar()) {
		if err := s.parseIdentifier(); err != nil {
			return err
		}
		CheckAndSetKeyword(s.nowToken)
		return nil

	}

	switch s.nowChar() {
	case '\'', '"':
		err := s.parseString()
		if err != nil {
			return err
		}
	case '(':
		*tokKind = TokLparen
		goto singleChar
	case '[':
		*tokKind = TokLbracket
		goto singleChar
	case '{':
		*tokKind = TokLbrace
		goto singleChar
	case ')':
		*tokKind = TokRparen
		goto singleChar
	case ']':
		*tokKind = TokRbracket
		goto singleChar
	case '}':
		*tokKind = TokRbrace
		goto singleChar
	case ',':
		*tokKind = TokComma
		goto singleChar
	case ';':
		*tokKind = TokSemi
		goto singleChar
	case '.':
		*tokKind = TokDot
		goto singleChar
	case ':':
		*tokKind = TokColon
		goto singleChar
	case '@':
		*tokKind = TokAt
		goto singleChar
	case '*':
		*tokOp = OpMult
		s.nextChar()
		if s.nowChar() == '*' {
			s.nextChar()
			*tokOp = OpPower
		}
		goto checkAssi
	case '/':
		s.nextChar()
		if s.nowChar() == '/' {
			s.nextChar()
			s.skipLineComment()
			goto again
		} else if s.nowChar() == '*' {
			s.nextChar()
			err := s.skipBlockComment()
			if err != nil {
				return err
			}
			goto again
		}
		*tokOp = OpDivi
		goto checkAssi
	case '#':
		if err := s.parseDocString(); err != nil {
			return err
		}
		return nil
	case '%':
		*tokOp = OpMod
		s.nextChar()
		goto checkAssi
	case '^':
		*tokOp = OpXor
		s.nextChar()
		goto checkAssi
	case '&':
		*tokOp = OpBand
		s.nextChar()
		goto checkAssi
	case '|':
		*tokOp = OpBor
		s.nextChar()
		goto checkAssi
	case '<':
		*tokKind = TokOperator
		*tokOp = OpLth
		s.nextChar()
		if s.nowChar() == '<' {
			s.nextChar()
			*tokOp = OpLshift
			goto checkAssi
		} else if s.nowChar() == '=' {
			s.nextChar()
			*tokOp = OpLeq
			*tokKind = TokOperator
			break
		}
		s.nowToken.Value = "<"
		return nil
	case '>':
		*tokKind = TokOperator
		*tokOp = OpGth
		s.nextChar()

		if s.nowChar() == '>' {
			s.nextChar()
			*tokOp = OpRshift
			goto checkAssi
		} else if s.nowChar() == '=' {
			s.nextChar()
			*tokOp = OpGeq
			*tokKind = TokOperator
			break
		}
		s.nowToken.Value = ">"
		return nil
	case '!':
		s.nextChar()
		if s.nowChar() == '=' {
			s.nextChar()
			*tokOp = OpUeq
			*tokKind = TokOperator
			break
		}
	case '+':
		*tokOp = OpPlus
		s.nextChar()
		goto checkAssi
	case '-':
		*tokOp = OpSub
		s.nextChar()
		goto checkAssi
	case '~':
		*tokOp = OpBng
		s.nextChar()
		goto checkAssi
	case '=':
		*tokOp = OpAssign
		*tokKind = TokOperator
		s.nextChar()
		if s.nowChar() == '=' {
			s.nextChar()
			*tokOp = OpEq
		}
		return nil
	default:
		return fmt.Errorf("Unknown character: %v ('%v')",
			int32(s.nowChar()), s.nowChar())
	}

	return nil

checkAssi:
	*tokKind = TokOperator
	if s.nowChar() == '=' {
		s.nextChar()
		*tokOp += AssiInc
	}

	return nil

singleChar:
	s.nowToken.Value = string(s.nowChar())
	s.nextChar()

	return nil
}

func (s *Scanner) skipLineComment() {
	s.nextChar()
	for s.nowChar() != '\n' && s.nowChar() != -1 {
		s.nextChar()
	}
	s.nextChar()
}

func (s *Scanner) skipBlockComment() error {
	s.nextChar()
	for s.nowChar() != -1 {
		if s.nextChar() == '*' && s.nextChar() == '/' {
			s.nextChar() // eat '/'
			return nil
		}
	}
	return fmt.Errorf("EOF while scanning comment block")
}

func (s *Scanner) NowToken() Token {
	return *s.nowToken
}

func (s *Scanner) GetTokenList() ([]Token, error) {
	tokList := make([]Token, 0)
	for {
		if err := s.NextToken(); err != nil {
			return nil, err
		}
		tok := s.NowToken()
		if tok.Kind == TokEOF {
			return tokList, nil
		}
		tokList = append(tokList, tok)
	}
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
