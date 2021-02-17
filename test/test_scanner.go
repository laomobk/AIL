package test

import (
	"ail/cmd/ail/core"
	"fmt"
	"os"
)

func testScanner() {
	source := readTestFile()
	scanner := core.NewScanner(source, "<test>")
	tokList := scanner.GetTokenList()

	if tokList == nil && core.ErrCheck() {
		e := core.ErrGetCurrentRuntimeError()
		if err := core.ErrPrintRuntimeError(os.Stderr, e); err != nil {
			panic(err)
		}
	}

	for _, tok := range tokList {
		fmt.Println(tok.String())
	}
}
