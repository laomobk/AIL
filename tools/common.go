package tools

import (
	"fmt"
	"strings"
)

func Assert(test bool, msg ...string) {
	if len(msg) == 0 {
		msg = []string{"No assert message"}
	}

	if !test {
		panic(fmt.Errorf("AssertionError: %s", strings.Join(msg, ", ")))
	}
}
