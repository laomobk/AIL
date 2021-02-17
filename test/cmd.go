package test

import (
	"fmt"
)

func CmdTestScanner(testCase string) {
	switch testCase {

	case "scanner":
		testScanner()
	default:
		fmt.Printf("ail test: invaild test case: %s\n", testCase)
	}
}
