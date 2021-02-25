package tests

import (
	"ail/cmd/ail/internal"
	"fmt"
	"testing"
)

func _RunParserWithSource(source string) internal.Node {
	tokList := _RunScannerWithSource(source)
	if tokList == nil {
		return nil
	}

	parser := internal.NewParser([]byte(source), tokList)
	node, err := parser.ParseCell()
	if err != nil {
		fmt.Printf(
			"    [ParserWarning] parser returns an Error: %s\n", err.Error())
		return nil
	}
	return node
}

func TestParseCell(test *testing.T) {

}
