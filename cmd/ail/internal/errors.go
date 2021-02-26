package internal

import (
	"ail/tools"
	"fmt"
	"io"
)

type RuntimeError struct {
	ErrType string
	ErrMsg  string

	FileName string
	Line     int
}

func (e *RuntimeError) Error() string {
	return e.ErrMsg
}

type SyntaxError struct {
	ErrMsg string
	Pos    Pos

	expecting bool // true if MORE (usually available in interactive mode)
}

func (e *SyntaxError) Error() string {
	return fmt.Sprintf("line %d, col: %d: %v", e.Pos.line, e.Pos.col, e.ErrMsg)
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
	errFormat := "%s: %s\n"
	return fmt.Sprintf(errFormat, rtErr.ErrType, rtErr.ErrMsg)
}

func ErrPrintRuntimeError(writer io.Writer, err *RuntimeError) error {
	_, e := writer.Write([]byte(ErrFormatRuntimeError(err)))
	return e
}

func ErrFormatSyntaxError(
	writer io.Writer, err *RuntimeError, source []byte) (string, error) {

	errFmt := "File \"%s\", line %v\n    %s\n%s\n"
	msg := ""
	line, e := tools.GetLineFromSource(err.Line, source)
	if e != nil {
		return "", e
	}

	if len(err.ErrMsg) > 0 {
		msg = fmt.Sprintf("%s: %s", err.ErrType, err.ErrMsg)
	} else {
		msg = err.ErrType
	}

	return fmt.Sprintf(errFmt, err.FileName, err.Line, line, msg), nil
}
