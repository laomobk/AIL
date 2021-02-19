package main

import (
	"ail/cmd/ail/internal"
	"testing"
)

func _RunScannerWithSource(source string) []internal.Token {
	scanner := internal.NewScanner([]byte(source), "<test>")
	return scanner.GetTokenList()
}

func _RunScannerAndCheck(source string, expectNil bool) bool {
	res := _RunScannerWithSource(source) == nil
	if expectNil {
		return !res
	}
	return res
}

func TestHexNumber(test *testing.T) {
}
