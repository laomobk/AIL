package tests

import (
	"ail/cmd/ail/internal"
	"ail/tools"
	"io/ioutil"
	"testing"
)

func ReadTestFile() string {
	b, err := ioutil.ReadFile("./test_data/test.ail")
	if err != nil {
		panic(err)
	}
	return string(b)
}

func FailIfNil(test *testing.T, target interface{}) bool {
	if target == nil {
		test.Fail()
	}
	return target == nil
}

func FailIfNotNil(test *testing.T, target interface{}) bool {
	if target != nil {
		test.Fail()
	}
	return target != nil
}

func FailIf(test *testing.T, b bool) {
	if b {
		test.Fail()
	}
}

func FailIfNot(test *testing.T, b bool) {
	if !b {
		test.Fail()
	}
}

func FailNowIf(test *testing.T, b bool) {
	if b {
		test.FailNow()
	}
}

func FailNowIfNot(test *testing.T, b bool) {
	if !b {
		test.FailNow()
	}
}

func FailNowIfNil(test *testing.T, target interface{}) {
	if target == nil {
		test.FailNow()
	}
}

func FailNowIfNotNil(test *testing.T, target interface{}) {
	if target != nil {
		test.FailNow()
	}
}

func PrintTree(node internal.Node) {
	println(tools.FormatValue(node))
}
