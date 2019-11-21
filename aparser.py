from alex import Token, TokenStream, Lex
import ast
from error import error_msg
from tokentype import *

_keywords_uc = (
        'PRINT', 'INPUT',
        'IF', 'THEN', 'BEGIN',
        'END', 'WHILE', 'DO',
        'UNTIL', 'LOOP', 'WEND',
        'FUN', 'IS'
        )

_end_signs_uc = ('WEND', 'END', 'ENDIF')

_keywords = tuple([x.lower() for x in _keywords_uc])
_end_signs = tuple([x.lower() for x in _end_signs_uc])

_cmp_op = (
        LAP_EQ, LAP_LARGER, LAP_SMALER,
        LAP_LARGER_EQ, LAP_SMALER_EQ,
        LAP_UEQ
        )

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
        return self.__tok_stream[self.__tc + 1]

    def __parse_bin_expr(self) -> ast.BinaryExprAST:
        pass

    @property
    def  __now_tok(self) -> Token:
        return self.__tok_stream[self.__tc]

    @property
    def __now_ln(self) -> int:
        try:
            return self.__now_tok.ln
        except AttributeError:
            return -1

    def __tok_is(self, tok :Token, value :str) -> bool:
        return tok.ttype != LAP_STRING and tok.value == value

    def __syntax_error(self, msg=None):
        error_msg(
                self.__now_ln,
                'SyntaxError%s' % ((' : ' if msg else '') + (msg if msg else '')),
                self.__filename)

    def __parse_arg_list(self) -> ast.ArgListAST:
        if self.__now_tok == ')':
            #空参数列表
            self.__next_tok()  # eat ')'
            return ast.ArgListAST([])
            
        a1 = self.__parse_binary_expr()

        if a1 is None:
            self.__syntax_error('Argument must be an expression!')

        alist = []
        alist.append(a1)

        while self.__now_tok == ',':
            self.__next_tok()
            a = self.__parse_binary_expr()
            if a is None:
                self.__syntax_error()
            alist.append(a)
        if self.__now_tok != ')':
            self.__syntax_error()
        self.__next_tok()

        return ast.ArgListAST(alist)

    def __parse_value_list(self) -> ast.ValueListAST:
        if self.__now_tok.ttype != LAP_IDENTIFIER:
            return self.__syntax_error()

        ida = self.__now_tok.value
        idl = [ida]

        self.__next_tok()

        while self.__now_tok == ',' and self.__now_tok.ttype != LAP_ENTER:
            self.__next_tok()

            if self.__now_tok.ttype != LAP_IDENTIFIER:
                self.__syntax_error()

            idl.append(self.__now_tok.value)

            self.__next_tok()

        return ast.ValueListAST(idl)

    def __parse_cell_or_call_expr(self) -> ast.ExprAST:
        if self.__now_tok == '(':
            self.__next_tok()
            e = self.__parse_binary_expr()
            
            if e is None:
                self.__syntax_error()
            
            if self.__now_tok != ')':
                self.__syntax_error()

            self.__next_tok()  # eat ')'
            return e

        nt = self.__now_tok

        name = nt.value  # it can be string, number or identifier

        net = self.__next_tok()

        if net != '(' and nt.ttype in (LAP_IDENTIFIER, LAP_NUMBER, LAP_STRING):  # is not call expr
            return ast.CellAST(name, nt.ttype)

        if net != '(':
            self.__syntax_error()

        self.__next_tok()

        al = self.__parse_arg_list()
        if al is None:
            self.__syntax_error()

        return ast.CallExprAST(name, al)

    def __parse_power_expr(self) -> ast.PowerExprAST:
        left = self.__parse_cell_or_call_expr()
        
        if left is None:
            self.__syntax_error()

        if self.__now_tok != '^':
            return left

        rl = []
        
        while self.__now_tok == '^':
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

        if self.__now_tok != 'MOD':
            return left

        rl = []
        
        while self.__now_tok == 'MOD':
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
        
        if self.__now_tok.ttype not in (LAP_MUIT, LAP_DIV):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (LAP_MUIT, LAP_DIV):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_mod_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.MuitDivExprAST(left_op, left, rl)

    def __parse_binary_expr(self) -> ast.BinaryExprAST:
        # if is assi expr
        if self.__now_tok.ttype == LAP_IDENTIFIER and self.__peek().ttype == LAP_ASSI:
            return self.__parse_define_expr()
            
        left = self.__parse_muit_div_expr()
        
        if left is None:
            self.__syntax_error()
        
        if self.__now_tok.ttype not in (LAP_PLUS, LAP_SUB):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (LAP_PLUS, LAP_SUB):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_muit_div_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.BinaryExprAST(left_op, left, rl)

    def __parse_print_expr(self) -> ast.PrintExprAST:
        self.__next_tok()  # eat 'PRINT'

        exp = self.__parse_binary_expr()

        if exp is None:
            self.__syntax_error()

        el = [exp]

        while self.__now_tok == ';':
            self.__next_tok()
            e = self.__parse_binary_expr()
            
            if e is None:
                self.__syntax_error()

            el.append(e)

        return ast.PrintExprAST(el)

    def __parse_input_expr(self) -> ast.InputExprAST:
        self.__next_tok()  # eat 'INPUT'

        msg = self.__parse_binary_expr()

        if msg is None:
            self.__syntax_error()

        if self.__now_tok != ';':
            return ast.InputExprAST(msg, ast.ValueListAST([]))

        if self.__next_tok().ttype == LAP_IDENTIFIER:
            vl = self.__parse_value_list()
        else:
            vl = ast.ValueListAST([])

        return ast.InputExprAST(msg, vl)

    def __parse_define_expr(self) ->ast.DefineExprAST:
            n = self.__now_tok.value
            self.__next_tok()
            self.__next_tok()

            v = self.__parse_binary_expr()

            return ast.DefineExprAST(n, v)

    def __parse_comp_test_expr(self) -> ast.CmpTestAST:
        left = self.__parse_binary_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype not in _cmp_op:
            return left

        rl = []

        while self.__now_tok.ttype in _cmp_op:
            now_op = self.__now_tok.value
            self.__next_tok()  # eat cmp op
            r = self.__parse_binary_expr()

            if r is None:
                self.__syntax_error()

            rl.append((now_op, r))

        return ast.CmpTestAST(left, rl)

    def __parse_and_test_expr(self) -> ast.AndTestAST:
        left = self.__parse_comp_test_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok != 'and':
            return left

        rl = []

        while self.__now_tok == 'and':
            self.__next_tok()   # eat 'and'
            r = self.__parse_comp_test_expr()

            if r is None:
                self.__syntax_error()

            rl.append(r)

        return ast.AndTestAST(left, rl)

    def __parse_or_test_expr(self) -> ast.OrTestAST:
        left = self.__parse_and_test_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok != 'or':
            return left

        rl = []

        while self.__now_tok == 'or':
            self.__next_tok()   # eat 'or'
            r = self.__parse_and_test_expr()

            if r is None:
                self.__syntax_error()

            rl.append(r)

        return ast.OrTestAST(left, rl)

    def __parse_test_expr(self) -> ast.TestExprAST:
        t = self.__parse_or_test_expr()
        
        if t is None:
            self.__syntax_error()

        return ast.TestExprAST(t)

    def __parse_if_else_expr(self) -> ast.IfExprAST:
        self.__next_tok()  # eat 'if'

        test = self.__parse_test_expr()

        if test is None:
            self.__syntax_error()

        if self.__now_tok != 'then':
            self.__syntax_error()

        block = self.__parse_block('then', 'endif', 
                "if block should starts with 'then'",
                "if block should ends with 'endif'")

        if block is None:
            self.__syntax_error()

        if self.__now_tok.ttype != LAP_ENTER:
            self.__syntax_error()

        if self.__peek() != 'else':
            return ast.IfExprAST(test, block, ast.BlockExprAST([]))

        self.__next_tok()  # move to else
        #self.__next_tok()  # eat else

        elseb = self.__parse_block('else', 'endif',
                "else block should starts with 'else'",
                "else block should ends with 'endif'")

        return ast.IfExprAST(test, block, elseb)

    def __parse_while_expr(self) -> ast.WhileExprAST:
        self.__next_tok()  # eat 'while'

        test = self.__parse_test_expr()

        if test is None:
            self.__syntax_error()

        block = self.__parse_block('then', 'wend', 
                'while block should starts with \'then\'',
                "while block should ends with 'wend'")

        if block is None:
            self.__syntax_error()

        if self.__now_tok.ttype != LAP_ENTER:
            self.__syntax_error()

        return ast.WhileExprAST(test, block)

    def __parse_do_loop_expr(self) -> ast.DoLoopExprAST:
        block = self.__parse_block('do', 'loop', 
                'do loop statement should starts with \'do\'',
                "do loop statement should ends with 'until'")

        if block is None:
            self.__syntax_error()

        if self.__now_tok != 'until':
            self.__syntax_error()

        self.__next_tok()  # eat until

        test = self.__parse_test_expr()

        return ast.DoLoopExprAST(test, block)

    def __parse_func_def_stmt(self) -> ast.FunctionDefineAST:
        self.__next_tok()  # eat 'fun'

        if self.__now_tok.ttype != LAP_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value

        if self.__next_tok() != '(':
            self.__syntax_error()

        self.__next_tok()  # eat '('

        if self.__now_tok == ')':
            arg_list = ast.ArgListAST([])  # empty arglist
            self.__next_tok()  # eat ')'
        else:
            arg_list = self.__parse_arg_list()

        block = self.__parse_block('is', 'end')

        return ast.FunctionDefineAST(name, arg_list, block)

    def __parse_continue_stmt(self) -> ast.ContinueAST:
        if self.__now_tok != 'continue':
            self.__syntax_error()

        self.__next_tok()  # eat 'continue'

        return ast.ContinueAST()

    def __parse_break_stmt(self) -> ast.BreakAST:
        if self.__now_tok != 'break':
            self.__syntax_error()

        self.__next_tok()  # eat 'break'

        return ast.BreakAST()

    def __parse_stmt(self, limit :tuple=()) -> ast.ExprAST:
        nt = self.__now_tok

        if nt == 'print':
            a = self.__parse_print_expr()

        elif nt == 'input':
            a = self.__parse_input_expr()

        elif nt == 'if':
            a = self.__parse_if_else_expr()

        elif nt == 'while':
            a = self.__parse_while_expr()

        elif nt == 'do':
            a = self.__parse_do_loop_expr()

        elif nt == 'continue':
            a = self.__parse_continue_stmt()

        elif nt == 'break':
            a = self.__parse_break_stmt()

        elif nt == 'fun':
            a = self.__parse_func_def_stmt()

        elif nt.ttype == LAP_IDENTIFIER and nt.value not in (_keywords + limit):
            a = self.__parse_binary_expr()

        elif nt.ttype == LAP_ENTER:
            self.__next_tok()
            return ast.NullLineAST()

        elif nt.ttype == LAP_EOF or (nt.value in _end_signs and nt.ttype != LAP_STRING):
            return ast.EOFAST()

        else:
            self.__syntax_error('Unknown statement starts with %s' % nt.value)

        if self.__now_tok.ttype != LAP_ENTER:  # a stmt should be end of ENTER
            self.__syntax_error('A statement should end with ENTER')

        self.__next_tok()  # eat enter

        return a

    def __parse_block(self, start='then', end='end', 
            start_msg :str=None, end_msg :str=None,
            start_enter=True) -> ast.BlockExprAST:

        if self.__now_tok != start:
            self.__syntax_error(start_msg)

        if start_enter and self.__next_tok().ttype != LAP_ENTER:
            self.__syntax_error()

        self.__next_tok()  # eat enter

        if self.__now_tok == end:   # empty block
            self.__next_tok()
            return ast.BlockExprAST([])

        first = self.__parse_stmt((start, end))

        if first is None:
            self.__syntax_error()

        elif isinstance(first, ast.EOFAST):
            self.__syntax_error(end_msg)
        
        stmtl = []

        if not isinstance(first, ast.NullLineAST):
            stmtl.append(first)

        while self.__now_tok != end:
            s = self.__parse_stmt((start, end))

            if s is None:
                self.__syntax_error()
            
            if not isinstance(s, ast.NullLineAST):
                stmtl.append(s)

            if isinstance(s, ast.EOFAST):
                self.__syntax_error(end_msg)

        self.__next_tok()  # eat end
        
        '''
        if self.__now_tok.ttype != LAP_ENTER:
            self.__syntax_error()
        '''

        #self.__next_tok()

        return ast.BlockExprAST(stmtl)

    def parse(self) -> ast.BlockExprAST:
        while self.__now_tok.ttype == LAP_ENTER:  # skip enter at beginning
            self.__next_tok()

        return self.__parse_block('begin', 'end', 
                'A program should starts with \'begin\'',
                "A program should ends with 'end'")

    def test(self):
        return self.parse()


def test_parse():
    import test_utils
    import pprint

    l = Lex('tests/test.ail')
    ts = l.lex()

    p = Parser(ts, 'tests/test.ail')
    t = p.test()
    pt = test_utils.make_ast_tree(t)
    pprint.pprint(pt)

if __name__ == '__main__':
    test_parse()
