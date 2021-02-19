package main

import "io/ioutil"

func readTestFile() []byte {
	b, err := ioutil.ReadFile("./test_data/test.ail")
	if err != nil {
		panic(err)
	}
	return b
}
