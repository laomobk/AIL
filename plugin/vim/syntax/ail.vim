" Vim syntax file
" Language:	AIL
" Maintainer:	Chen hongbo
" Create time:  Sep 28 2020
" Last Change: Jul 21 2021

if exists("b:current_syntax")
  finish
endif

syn keyword ailStmt	if else elif
syn keyword ailStmt	then end endif is begin wend
syn keyword ailStmt	extends
syn keyword ailStmt struct func fun class nextgroup=ailFunction skipwhite
syn keyword ailStmt	return assert
syn keyword ailStmt	print input
syn keyword ailStmt try catch finally
syn keyword ailStmt break continue throw
syn keyword ailStmt import load as from
syn keyword ailStmt global nonlocal
syn keyword ailStmt get set init new getattr setattr delattr getitem setitem delitem del
syn keyword ailStmt mod and not or
syn keyword ailStmt match namespace with when yield from

syn keyword ailConst false true __main__

syn keyword ailRepeat while for do loop until foreach in

syn keyword ailFunc abs
syn keyword ailFunc ng
syn keyword ailFunc int_input
syn keyword ailFunc __version__
syn keyword ailFunc __main_version__
syn keyword ailFunc chr
syn keyword ailFunc ord
syn keyword ailFunc hex
syn keyword ailFunc make_type
syn keyword ailFunc null
syn keyword ailFunc len
syn keyword ailFunc equal
syn keyword ailFunc type
syn keyword ailFunc array
syn keyword ailFunc equal_type
syn keyword ailFunc isinstance
syn keyword ailFunc str
syn keyword ailFunc repr
syn keyword ailFunc _get_ccom
syn keyword ailFunc open
syn keyword ailFunc int
syn keyword ailFunc float
syn keyword ailFunc addr
syn keyword ailFunc fnum

syn keyword ailType Integer Float String Boolean Array Map

" Python highlighting support:
" Python builtin Exception, provided by VIM builtin Python Syntax Highlighting file.

syn keyword pythonExceptions	BaseException Exception
syn keyword pythonExceptions	ArithmeticError BufferError
syn keyword pythonExceptions	LookupError
syn keyword pythonExceptions	EnvironmentError StandardError
syn keyword pythonExceptions	AssertionError AttributeError
syn keyword pythonExceptions	EOFError FloatingPointError GeneratorExit
syn keyword pythonExceptions	ImportError IndentationError
syn keyword pythonExceptions	IndexError KeyError KeyboardInterrupt
syn keyword pythonExceptions	MemoryError NameError NotImplementedError
syn keyword pythonExceptions	OSError OverflowError ReferenceError
syn keyword pythonExceptions	RuntimeError StopIteration SyntaxError
syn keyword pythonExceptions	SystemError SystemExit TabError TypeError
syn keyword pythonExceptions	UnboundLocalError UnicodeError
syn keyword pythonExceptions	UnicodeDecodeError UnicodeEncodeError
syn keyword pythonExceptions	UnicodeTranslateError ValueError
syn keyword pythonExceptions	ZeroDivisionError
syn keyword pythonExceptions	BlockingIOError BrokenPipeError
syn keyword pythonExceptions	ChildProcessError ConnectionAbortedError
syn keyword pythonExceptions	ConnectionError ConnectionRefusedError
syn keyword pythonExceptions	ConnectionResetError FileExistsError
syn keyword pythonExceptions	FileNotFoundError InterruptedError
syn keyword pythonExceptions	IsADirectoryError NotADirectoryError
syn keyword pythonExceptions	PermissionError ProcessLookupError
syn keyword pythonExceptions	RecursionError StopAsyncIteration
syn keyword pythonExceptions	TimeoutError
syn keyword pythonExceptions	IOError VMSError WindowsError
syn keyword pythonExceptions	BytesWarning DeprecationWarning FutureWarning
syn keyword pythonExceptions	ImportWarning PendingDeprecationWarning
syn keyword pythonExceptions	RuntimeWarning SyntaxWarning UnicodeWarning
syn keyword pythonExceptions	UserWarning Warning
syn keyword pythonExceptions	ResourceWarning

" built-in constants
" 'False', 'True', and 'None' are also reserved words in Python 3
syn keyword pythonBuiltin	False True None
syn keyword pythonBuiltin	NotImplemented Ellipsis __debug__
syn keyword pythonBuiltin	abs all any bin bool bytearray callable chr
syn keyword pythonBuiltin	classmethod compile complex delattr dict dir
syn keyword pythonBuiltin	divmod enumerate eval filter float format
syn keyword pythonBuiltin	frozenset getattr globals hasattr hash
syn keyword pythonBuiltin	help hex id int isinstance
syn keyword pythonBuiltin	issubclass iter len list locals map max
syn keyword pythonBuiltin	memoryview min next object oct open ord pow
syn keyword pythonBuiltin	property range repr reversed round set
syn keyword pythonBuiltin	setattr slice sorted staticmethod str
syn keyword pythonBuiltin	sum super tuple type vars zip __import__
syn keyword pythonBuiltin	basestring cmp execfile file
syn keyword pythonBuiltin	long raw_input reduce reload unichr
syn keyword pythonBuiltin	unicode xrange
syn keyword pythonBuiltin	ascii bytes exec
syn keyword pythonBuiltin	apply buffer coerce intern
syn match   pythonAttribute	/\.\h\w*/hs=s+1
	\ contains=ALLBUT,pythonBuiltin,pythonFunction,pythonAsync
	\ transparent
syn match   pythonDecorator	"@" display contained
syn match   pythonDecoratorName	"@\s*\h\%(\w\|\.\)*" display contains=pythonDecorator

syn match  ailNumber		"\<\d\+\>"
syn match  ailNumber		"\<\d\+\.\d*\>"
syn match  ailNumber		"\.\d\+\>"

syn match ailComment "\v(\/\/).*$"
syn match ailComment "\v(#).*$"

syn region ailString start=/\v"/ skip=/\v\\./ end=/\v"/
syn region ailString start=/\v'/ skip=/\v\\./ end=/\v'/
syn region ailString start=/\v`/ skip=/\v\\./ end=/\v`/

syn region ailComment start=/\v(\/\*)/ skip=/\v\\./ end=/\v(\*\/)/

syn match ailFunction "\h\w*" display contained

hi def link ailNumber		Number
hi def link ailStmt		    Statement
hi def link ailString		String
hi def link ailComment		Comment
hi def link ailFunc		    Identifier
hi def link ailConst		Identifier
hi def link ailRepeat       Repeat
hi def link ailType         Type
" hi def link ailFunction     Function

hi def link pythonExceptions    Structure
hi def link pythonBuiltin      Identifier
hi def link pythonDecorator		Define
hi def link pythonDecoratorName		Function

let b:current_syntax = "ail"

