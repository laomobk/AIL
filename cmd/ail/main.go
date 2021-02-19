package main

import (
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
	fmt.Println("ail: building...")
}
