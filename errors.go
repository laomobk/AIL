package ail

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
