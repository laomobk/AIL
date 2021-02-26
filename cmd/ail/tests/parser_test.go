package tests

import (
	"ail/cmd/ail/internal"
	"ail/tools"
	"fmt"
	"testing"
)

func _RunParserWithSource(source string) internal.Node {
	tokList := _RunScannerWithSource(source)
	if tokList == nil {
		return nil
	}

	parser := internal.NewParserWithSource([]byte(source), tokList)
	node, err := parser.Parse()
	if err != nil {
		fmt.Printf(
			"    [ParserWarning] parser returns an Error: %s\n", err.Error())
		return nil
	}
	return node
}

func _CheckRun(test *testing.T, node internal.Node, err error) internal.Node {
	if err != nil {
		test.Logf(
			"    [ParserWarning] parser returns an Error: %s\n", err.Error())
		return nil
	}
	return node
}

func _CheckRunFail(
	test *testing.T, node internal.Node, err error, printTree bool) internal.Node {

	if printTree {
		test.Log(tools.FormatValue(node))
	}

	if err != nil {
		test.Logf(
			"[ParserWarning] parser returns an Error: %s\n", err.Error())
		test.FailNow()
	}
	return node
}

func _NewParser(source string) *internal.Parser {
	tokList := _RunScannerWithSource(source)
	if tokList == nil {
		return nil
	}

	return internal.NewParserWithSource([]byte(source), tokList)
}

func TestParseCell(test *testing.T) {

	func() {
		test.Log("parsing identifier")
		expr, err := _NewParser("Nezha").ParseCell()
		cell, ok := _CheckRunFail(test, expr, err, false).(*internal.CellExpr)
		FailNowIfNot(test, ok)

		FailNowIfNot(test,
			cell.Token.Value == "Nezha" &&
				cell.Token.Kind == internal.TokIdentifier,
		)
	}()

	func() {
		test.Log("parsing integer")
		expr, err := _NewParser("3").ParseCell()
		cell, ok := _CheckRunFail(test, expr, err, false).(*internal.CellExpr)
		FailNowIfNot(test, ok)

		FailNowIfNot(test,
			cell.Token.Value == "3" &&
				cell.Token.Kind == internal.TokNumber &&
				cell.NumFlags&internal.NumInteger != 0,
		)
	}()

	func() {
		test.Log("parsing string")
		expr, err := _NewParser("'我命由我不由天'").ParseCell()
		cell, ok := _CheckRunFail(test, expr, err, false).(*internal.CellExpr)
		FailNowIfNot(test, ok)

		FailNowIfNot(test,
			cell.Token.Value == "我命由我不由天" &&
				cell.Token.Kind == internal.TokString,
		)
	}()
}

func TestParseExpr(test *testing.T) {
	source := ReadTestFile()
	tmp, err := _NewParser(source).ParseExpression()
	_ = _CheckRunFail(test, tmp, err, true)
}

func TestParseFile(test *testing.T) {
	source := ReadTestFile()
	tmp, err := _NewParser(source).Parse()
	_ = _CheckRunFail(test, tmp, err, true)
}
