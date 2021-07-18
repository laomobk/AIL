" Vim syntax file
" Language:	AIL
" Maintainer:	Chen hongbo
" Last Change:  2020 Sep 28

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
syn keyword ailStmt import load
syn keyword ailStmt global nonlocal
syn keyword ailStmt get set init new getattr setattr delattr getitem setitem delitem del
syn keyword ailStmt mod and not or
syn keyword ailStmt match namespace

syn keyword ailConst false true __main__

syn keyword ailRepeat while for do loop until

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

syn match  ailNumber		"\<\d\+\>"
syn match  ailNumber		"\<\d\+\.\d*\>"
syn match  ailNumber		"\.\d\+\>"

syn match ailComment "\v(\/\/).*$"
syn match ailComment "\v(#).*$"

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
hi def link ailType         Type

syn match ailFunction "\h\w*" display contained

let b:current_syntax = "ail"

