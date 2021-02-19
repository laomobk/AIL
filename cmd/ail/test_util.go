package main

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

func _FailIfNil(test *testing.T, target interface{}) {
	if target == nil {
		test.Fail()
	}
}

func _FailIfNotNil(test *testing.T, target interface{}) {
	if target != nil {
		test.Fail()
	}
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
