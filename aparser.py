from alex import Token, TokenStream
import ast
from error import error_msg
from tokentype import *

class Parser:
    def __init__(self, ts :TokenStream, filename :str):
        self.__filename = filename
        self.__tok_stream = ts
        self.__tok_list = ts.token_list

        self.__tc = 0

    def __mov_tp(self, step=1):
        self.__tc += step

    def __next_tok(self) -> Token:
        self.__tc += 1
        return self.__tok_stream[self.__tc]

    def __peek(self, step=1) -> Token:
        return self.__tok_stream[self.__tok_stream + 1]

    def __parse_bin_expr(self) -> ast.BinaryExprAST:
        pass

    @property
    def  __now_tok(self) -> Token:
        return self.__tok_stream[self.__tc]

    @property
    def __now_ln(self) -> int:
        return self.__now_tok.ln

    def __syntax_error(self):
        error_msg(
                self.__now_ln,
                'SyntaxError',
                self.__filename)

    def __parse_arg_list(self) -> ast.ArgListAST:
        if self.__now_tok.value == ')':
            #空参数列表
            self.__next_tok()  # eat ')'
            return ast.ArgListAST([])
            
        a1 = self.__parse_bin_expr()

        if a1 is None:
            self.__syntax_error()

        alist = []
        alist.append(a1)

        while self.__now_tok.value == ',':
            a = self.__parse_bin_expr()
            if a is None:
                self.__syntax_error()
            alist.append(a)
        if self.__now_tok.value != ')':
            self.__syntax_error()
        self.__next_tok()

        return ast.ArgListAST(alist)

    def __parse_cell_or_call_expr(self) -> ast.ExprAST:
        nt = self.__now_tok

        if nt.ttype != LAP_IDENTIFIER:
            self.__syntax_error()

        name = nt.value  # it can be string, number or identifier

        if self.__next_tok().value != '(':  # is not call expr
            self.__next_tok()
            return ast.CellAST(name)

        self.__next_tok()  # eat '('

        al = self.__parse_arg_list()
        if al is None:
            self.__syntax_error()

        return ast.CallExprAST(name, al)


    def __parse_power_expr(self) -> ast.PowerExprAST:
        left = self.__parse_cell_or_call_expr
        
        if left is None:
            self.__syntax_error()

        self.__now_tok.value != '^':
            return left

        rl = []
        
        while self.__now_tok.value == '^'
