package main

import (
	"ail/test"
	"flag"
	"fmt"
)

type Flag struct {
	Available bool
	Value     string
}

func (f *Flag) String() string {
	return "<AIL Command TestFlag>"
}

func (f *Flag) Set(s string) error {
	f.Value = s
	f.Available = true
	return nil
}

func main() {
	testFlag := new(Flag)

	flag.Var(testFlag, "test", "test case")

	flag.Parse()

	if testFlag.Available {
		test.CmdTestScanner(testFlag.Value)
	} else {
		fmt.Println("ail: building...")
	}
}
