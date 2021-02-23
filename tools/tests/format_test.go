package tests

import (
	"ail/tools"
	"fmt"
	"testing"
)

type _Info interface{}

type info struct {
	Name string
	Age  int
}

type person struct {
	info _Info
}

func TestFormatStruct(test *testing.T) {
	fmt.Println(tools.FormatStruct(person{
		&info{"Aobing", 3},
	},
	))
}
