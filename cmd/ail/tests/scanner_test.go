package tests

import (
	"ail/cmd/ail/internal"
	"fmt"
	"testing"
)

func _RunScannerWithSource(source string) []internal.Token {
	scanner := internal.NewScanner([]byte(source), "<test>")
	tokList, err := scanner.GetTokenList()

	if err == nil {
		return tokList
	} else {
		fmt.Printf(
			"    [ScannerWarning] scanner returns an Error: %s\n", err.Error())
		return nil
	}
}

func _CheckNumber(source string, checker func(*internal.Token) bool) bool {
	return _CheckSingleToken(source, checker, internal.TokNumber)
}

func _CheckSingleToken(
	source string, checker func(*internal.Token) bool, kind int) bool {

	var tok *internal.Token

	fmt.Printf("  [CheckSingleToken] check source: %s\n", source)

	if tokList := _RunScannerWithSource(source); tokList != nil {
		if len(tokList) != 1 {
			fmt.Printf("    [CheckSingleToken][FAILED] len(tokList) != 1\n")
			fmt.Printf("    [CheckSingleToken] tokList:\n")
			if len(tokList) == 0 {
				fmt.Println("        <empty>")
				return false
			}

			for i, t := range tokList {
				fmt.Printf("       %v: %s\n", i, t.String())
			}

			return false
		}
		tok = &tokList[0]
	} else {
		fmt.Printf("    [CheckSingleToken][FAILED] tokList == nil\n")
		return false
	}

	res := tok.Kind == kind && checker(tok)

	fmt.Printf("    [CheckSingleToken] result: %v\n", res)
	return res
}

func TestEmptySource(test *testing.T) {
	FailIfNil(test, _RunScannerWithSource(""))
}

func TestSourceOnlyNewLine(test *testing.T) {
	FailIfNil(test, _RunScannerWithSource("\n"))
}

func TestSourceWithReturn(test *testing.T) {
	FailIfNil(test, _RunScannerWithSource("\r"))
}

func TestSourceWithChinese(test *testing.T) {
	if tokList := _RunScannerWithSource("我命由我不由天"); tokList != nil {
		FailIf(test,
			len(tokList) != 1 || (tokList[0].Value != "我命由我不由天" ||
				tokList[0].Kind != internal.TokIdentifier))
	} else {
		test.Fail()
	}
}

func TestASCIICharString(test *testing.T) {
	for ch := 0; ch <= 255; ch++ {
		if ch == 34 {
			continue
		}
		// fmt.Printf("Testing char: %v\n", ch)
		FailIfNil(test, _RunScannerWithSource(
			fmt.Sprintf("\"%s\"", string(rune(ch)))))
	}
}

func TestEmptyString(test *testing.T) {
	FailIfNil(test, _RunScannerWithSource("\"\""))
	FailIfNil(test, _RunScannerWithSource("''"))
}

func TestMultipleLineString(test *testing.T) {
	FailIfNil(test, _RunScannerWithSource("'\n\nFoo\nBar\n\n'"))
	FailIfNil(test, _RunScannerWithSource("\"\n\nFoo\nBar\n\n\""))
}

func TestChineseCharacterString(test *testing.T) {
	if tokList := _RunScannerWithSource("'我命由我不由天'"); tokList != nil {
		FailIf(
			test,
			len(tokList) != 1 || tokList[0].Value != "我命由我不由天" ||
				tokList[0].Kind != internal.TokString)
	} else {
		test.Fail()
	}
}

func TestNumber(test *testing.T) {
	FailIfNot(test, _CheckNumber("726", func(token *internal.Token) bool {
		return token.NumBase == 10 && token.NumTypeFlags == internal.NumInteger &&
			token.Value == "726"
	}))
	FailIfNot(test, _CheckNumber("7.26", func(token *internal.Token) bool {
		return token.NumBase == 10 && token.NumTypeFlags == internal.NumFloat &&
			token.Value == "7.26"
	}))
	FailIfNot(test, _CheckNumber("10e26", func(token *internal.Token) bool {
		return token.NumTypeFlags == internal.NumScience && token.Value == "10" &&
			token.NumPower == "26"
	}))
	FailIfNot(test, _CheckNumber("10e26", func(token *internal.Token) bool {
		return token.NumTypeFlags == internal.NumScience && token.Value == "10" &&
			token.NumPower == "26"
	}))
	FailIfNot(test, _CheckNumber("1.0e26", func(token *internal.Token) bool {
		return token.NumTypeFlags&internal.NumFloat != 0 &&
			token.Value == "1.0" &&
			token.NumPower == "26"
	}))
	FailIfNot(test, _CheckNumber("0xcafebabe", func(token *internal.Token) bool {
		return token.Value == "cafebabe" && token.NumBase == 16
	}))
	FailIfNot(test, _CheckNumber("0x726", func(token *internal.Token) bool {
		return token.Value == "726" && token.NumBase == 16
	}))
	FailIfNot(test, _CheckNumber("0xabc1026", func(token *internal.Token) bool {
		return token.Value == "abc1026" && token.NumBase == 16
	}))
	FailIfNot(test, _CheckNumber("0o1326", func(token *internal.Token) bool {
		return token.Value == "1326" && token.NumBase == 8
	}))
	FailIfNot(test, _CheckNumber("0b1011010110", func(token *internal.Token) bool {
		return token.Value == "1011010110" && token.NumBase == 2
	}))
}

func TestBadFloatNumber(test *testing.T) {
	FailIfNot(test, len(_RunScannerWithSource("7.2.6")) == 0)
	FailIfNot(test, len(_RunScannerWithSource("7.26.")) == 0)
}

func TestBadHexNumber(test *testing.T) {
	FailIfNot(test, len(_RunScannerWithSource("0xabcdefg")) == 0)
	FailIfNot(test, len(_RunScannerWithSource("0xabcd.7")) == 0)
	FailIfNot(test, len(_RunScannerWithSource("0xabcd.ef")) == 0)
}

func TestBadOctNumber(test *testing.T) {
	FailIfNot(test, len(_RunScannerWithSource("0o900")) == 0)
	FailIfNot(test, len(_RunScannerWithSource("0o70.0")) == 0)
}

func TestBadBinNumber(test *testing.T) {
	FailIfNot(test, len(_RunScannerWithSource("0b900")) == 0)
	FailIfNot(test, len(_RunScannerWithSource("0b0.10")) == 0)
}

func TestKeywords(test *testing.T) {
	for k, v := range internal.KeywordMap {
		if k == "and" || k == "or" || k == "not" {
			continue
		}

		FailIfNot(test, _CheckSingleToken(k, func(token *internal.Token) bool {
			res := token.Kind == v
			fmt.Printf("  [CheckKeyword] %s -- %v\n", k, v)
			return res
		}, v))
	}
}

func TestOperators(test *testing.T) {
	for k, v := range internal.OpMap {
		FailIfNot(test, _CheckSingleToken(k, func(token *internal.Token) bool {
			res := token.Op == v
			fmt.Printf("  [CheckOperator] %s -- %v\n", k, v)
			return res
		}, internal.TokOperator))
	}
}
