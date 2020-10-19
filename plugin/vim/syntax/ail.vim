" Vim syntax file
" Language:	AIL
" Maintainer:	Chen hongbo
" Last Change:  2020 Sep 28

if exists("b:current_syntax")
  finish
endif


syn keyword ailStmt	if else elif
syn keyword ailStmt	then end endif is begin wend
syn keyword ailStmt	fun struct
syn keyword ailStmt	return assert
syn keyword ailStmt	print input
syn keyword ailStmt try catch
syn keyword ailStmt break continue
syn keyword ailStmt import load
syn keyword ailStmt global nonlocal

syn keyword ailConst false true

syn keyword ailRepeat	while for do loop until

syn keyword ailFunc abs
syn keyword ailFunc ng
syn keyword ailFunc int_input
syn keyword ailFunc __version__
syn keyword ailFunc __main_version__
syn keyword ailFunc chr
syn keyword ailFunc ord
syn keyword ailFunc hex
syn keyword ailFunc make_type
syn keyword ailFunc new
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

syn match  ailNumber		"\<\d\+\>"
syn match  ailNumber		"\<\d\+\.\d*\>"
syn match  ailNumber		"\.\d\+\>"

syn match ailComment "\v(\/\/).*$"

syn region ailString start=/\v"/ skip=/\v\\./ end=/\v"/
syn region ailString start=/\v'/ skip=/\v\\./ end=/\v'/

syn region ailComment start=/\v(\/\*)/ skip=/\v\\./ end=/\v(\*\/)/

hi def link ailNumber		Number
hi def link ailStmt		    Statement
hi def link ailString		String
hi def link ailComment		Comment
hi def link ailFunc		    Identifier
hi def link ailConst		Identifier
hi def link ailRepeat       Repeat

let b:current_syntax = "ail"

