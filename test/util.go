package test

import "io/ioutil"

func readTestFile() []byte {
	b, err := ioutil.ReadFile("./test.ail")
	if err != nil {
		panic(err)
	}
	return b
}
