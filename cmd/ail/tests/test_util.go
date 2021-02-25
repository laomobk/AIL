package tests

import (
	"io/ioutil"
	"testing"
)

func readTestFile() []byte {
	b, err := ioutil.ReadFile("./test_data/test.ail")
	if err != nil {
		panic(err)
	}
	return b
}

func _FailIfNil(test *testing.T, target interface{}) bool {
	if target == nil {
		test.Fail()
	}
	return target == nil
}

func _FailIfNotNil(test *testing.T, target interface{}) bool {
	if target != nil {
		test.Fail()
	}
	return target != nil
}

func _FailIf(test *testing.T, b bool) {
	if b {
		test.Fail()
	}
}

func _FailIfNot(test *testing.T, b bool) {
	if !b {
		test.Fail()
	}
}
