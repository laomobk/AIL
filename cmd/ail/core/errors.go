package core

import (
	"fmt"
	"io"
)

type RuntimeError struct {
	ErrType string
	ErrMsg  string

	FileName string
	Line     int
}

var errStack []*RuntimeError
var errOccurred bool
var currentError *RuntimeError

func ErrSetError(error *RuntimeError) {
	currentError = error
	errOccurred = true
}

func ErrNewRuntimeErrorTM(errType, errMsg string) *RuntimeError {
	return &RuntimeError{
		errType,
		errMsg,
		"<no file name>",
		0,
	}
}

func ErrNewRuntimeErrorTMFL(errType, errMsg, fileName string, line int) *RuntimeError {
	return &RuntimeError{
		errType,
		errMsg,
		fileName,
		line,
	}
}

func ErrCheck() bool {
	return (errOccurred || len(errStack) > 0) && currentError != nil
}

func ErrGetCurrentRuntimeError() *RuntimeError {
	return currentError
}

func ErrFormatRuntimeError(rtErr *RuntimeError) string {
	errFormat := "%s: %s"
	return fmt.Sprintf(errFormat, rtErr.ErrType, rtErr.ErrMsg)
}

func ErrPrintRuntimeError(writer io.Writer, err *RuntimeError) error {
	_, e := writer.Write([]byte(ErrFormatRuntimeError(err)))
	if e != nil {
		return e
	}
	return nil
}
