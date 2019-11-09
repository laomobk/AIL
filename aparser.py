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

        name = nt.value  # it can be string, number or identifier

        if self.__next_tok().value != '(' and nt.ttype != LAP_IDENTIFIER:  # is not call expr
            self.__next_tok()
            return ast.CellAST(name)

        self.__next_tok()  # eat '('

        al = self.__parse_arg_list()
        if al is None:
            self.__syntax_error()

        return ast.CallExprAST(name, al)


    def __parse_power_expr(self) -> ast.PowerExprAST:
        left = self.__parse_cell_or_call_expr()
        
        if left is None:
            self.__syntax_error()

        if self.__now_tok.value != '^':
            return left

        rl = []
        
        while self.__now_tok.value == '^':
            self.__next_tok()
            r = self.__parse_cell_or_call_expr()
            if r is None:
                self.__syntax_error()
            rl.append(r)
        return ast.PowerExprAST(left, rl)


    def __parse_mod_expr(self) -> ast.ModExprAST:
        left = self.__parse_power_expr()
        
        if left is None:
            self.__syntax_error()

        if self.__now_tok.value != 'MOD':
            return left

        rl = []
        
        while self.__now_tok.value == 'MOD':
            self.__next_tok()
            r = self.__parse_power_expr()
            if r is None:
                self.__syntax_error()
            rl.append(r)
        return ast.ModExprAST(left, rl)


    def __parse_muit_div_expr(self) -> ast.MuitDivExprAST:
        left = self.__parse_mod_expr()
        
        if left is None:
            self.__syntax_error()
        
        if self.__now_tok.value not in ('*', '/'):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.value in ('*', '/'):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_mod_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.MuitDivExprAST(left_op, left, rl)


    def __parse_binary_expr(self) -> ast.BinaryExprAST:
        left = self.__parse_muit_div_expr()
        
        if left is None:
            self.__syntax_error()
        
        if self.__now_tok.value not in ('+', '-'):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.value in ('+', '-'):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_muit_div_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.BinaryExprAST(left_op, left, rl)
 
