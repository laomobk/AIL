package tools

import (
	"bufio"
	"bytes"
	"io"
)

func GetLineFromSource(line int, source []byte) (string, error) {
	if line <= 0 {
		return "", nil
	}

	bReader := bytes.NewReader(source)
	reader := bufio.NewReader(bReader)

	for lno := 1; ; lno++ {
		ln, _, err := reader.ReadLine()
		if err == io.EOF {
			return "", nil
		}

		if err != nil {
			return "", err
		}
		if lno == line {
			return string(ln), nil
		}
	}
}
