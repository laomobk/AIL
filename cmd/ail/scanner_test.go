package main

import (
	"ail/cmd/ail/internal"
	"fmt"
	"testing"
)

func _RunScannerWithSource(source string) []internal.Token {
	scanner := internal.NewScanner([]byte(source), "<test>")
	if tokList, err := scanner.GetTokenList(); err == nil {
		return tokList
	} else {
		return nil
	}
}

func _RunScannerAndCheck(source string, expectNil bool) bool {
	res := _RunScannerWithSource(source) != nil
	if expectNil {
		return !res
	}
	return res
}

func _CheckNumber(source string, checker func(*internal.Token) bool) bool {
	if tokList := _RunScannerWithSource(source); tokList != nil {
		return len(tokList) == 1 && tokList[0].Kind == internal.TokNumber &&
			checker(&tokList[0])
	} else {
		return false
	}
}

func TestEmptySource(test *testing.T) {
	_FailIfNil(test, _RunScannerWithSource(""))
}

func TestSourceOnlyNewLine(test *testing.T) {
	_FailIfNil(test, _RunScannerWithSource("\n"))
}

func TestSourceWithReturn(test *testing.T) {
	_FailIfNil(test, _RunScannerWithSource("\r"))
}

func TestSourceWithChinese(test *testing.T) {
	if tokList := _RunScannerWithSource("我命由我不由天"); tokList != nil {
		_FailIf(test,
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
		_FailIfNil(test, _RunScannerWithSource(
			fmt.Sprintf("\"%s\"", string(rune(ch)))))
	}
}

func TestEmptyString(test *testing.T) {
	_FailIfNil(test, _RunScannerWithSource("\"\""))
	_FailIfNil(test, _RunScannerWithSource("''"))
}

func TestMultipleLineString(test *testing.T) {
	_FailIfNil(test, _RunScannerWithSource("'\n\nFoo\nBar\n\n'"))
	_FailIfNil(test, _RunScannerWithSource("\"\n\nFoo\nBar\n\n\""))
}

func TestChineseCharacterString(test *testing.T) {
	if tokList := _RunScannerWithSource("'我命由我不由天'"); tokList != nil {
		_FailIf(test,
			len(tokList) != 1 || tokList[0].Value != "我命由我不由天" ||
				tokList[0].Kind != internal.TokString)
	} else {
		test.Fail()
	}
}

func TestNumber(test *testing.T) {
	_FailIfNot(test, _CheckNumber("726", func(token *internal.Token) bool {
		return token.NumBase == 10 && token.NumTypeFlags == internal.NumInteger &&
			token.Value == "726"
	}))
	_FailIfNot(test, _CheckNumber("7.26", func(token *internal.Token) bool {
		return token.NumBase == 10 && token.NumTypeFlags == internal.NumFloat &&
			token.Value == "7.26"
	}))
	_FailIf(test, _CheckNumber("7.2.6", func(token *internal.Token) bool {
		// This test must be FALSE!!
		return token.NumBase == 10 && token.NumTypeFlags == internal.NumFloat &&
			token.Value == "7.2.6"
	}))
	_FailIfNot(test, _CheckNumber("10e26", func(token *internal.Token) bool {
		return token.NumTypeFlags == internal.NumScience && token.Value == "10" &&
			token.NumPower == "26"
	}))
	_FailIfNot(test, _CheckNumber("10e26", func(token *internal.Token) bool {
		return token.NumTypeFlags == internal.NumScience && token.Value == "10" &&
			token.NumPower == "26"
	}))
	_FailIfNot(test, _CheckNumber("1.0e26", func(token *internal.Token) bool {
		return token.NumTypeFlags|internal.NumFloat != 0 &&
			token.Value == "1.0" &&
			token.NumPower == "26"
	}))
}
