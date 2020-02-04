from alex import Token, TokenStream, Lex
import asts as ast
from error import error_msg
from tokentype import *

__author__ = 'LaomoBK'

_keywords_uc = (
        'PRINT', 'INPUT',
        'IF', 'THEN', 'BEGIN',
        'END', 'WHILE', 'DO',
        'UNTIL', 'LOOP', 'WEND',
        'FUN', 'IS', 'ELSE',  'ENDIF', 'LOAD'
        )

_end_signs_uc = ('WEND', 'END', 'ENDIF', 'ELSE', 'ELIF')

_keywords = tuple([x.lower() for x in _keywords_uc])
_end_signs = tuple([x.lower() for x in _end_signs_uc])

_cmp_op = (
        LAP_EQ, LAP_LARGER, LAP_SMALER,
        LAP_LARGER_EQ, LAP_SMALER_EQ,
        LAP_UEQ
        )

_FROM_MAIN = 0
_FROM_FUNC = 1

class Parser:
    def __init__(self, ts :TokenStream, filename :str):
        self.__filename = filename
        self.__tok_stream = ts
        self.__tok_list = ts.token_list

        self.__tc = 0

        self.__level = 0  # level 0

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
            return ast.ArgListAST([], self.__now_ln)
            
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

        return ast.ArgListAST(alist, self.__now_ln)

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

        return ast.ValueListAST(idl, self.__now_ln)

    def __parse_item_list(self) -> ast.ItemListAST:
        if self.__now_tok.ttype == LAP_LRBASKET:
            return ast.ItemListAST([], self.__now_ln)

        il = []

        while self.__now_tok.ttype != LAP_LRBASKET:
            eitem = self.__parse_binary_expr()
            
            if eitem is None:
                self.__syntax_error()

            il.append(eitem)

            if self.__now_tok.ttype == LAP_COMMA:        
                self.__next_tok()

        return ast.ItemListAST(il, self.__now_ln)

    def __parse_array_expr(self) -> ast.ArrayAST:
        if self.__now_tok.ttype != LAP_LLBASKET:
            self.__syntax_error()

        self.__next_tok()  # eat '{'

        if self.__now_tok.ttype == LAP_LRBASKET:
            self.__next_tok()  # eat '{'
            return ast.ArrayAST(ast.ItemListAST([], self.__now_ln), self.__now_ln)
        
        items = self.__parse_item_list()

        if self.__now_tok.ttype != LAP_LRBASKET:
            self.__syntax_error()

        self.__next_tok()

        if items is None:
            self.__syntax_error()

        return ast.ArrayAST(items, self.__now_ln)

    def __parse_cell_or_call_expr(self) -> ast.SubscriptExprAST:
        # in fact, it is for subscript

        ca = self.__parse_low_cell_or_call_expr()

        if self.__now_tok.ttype == LAP_MLBASKET:
            self.__next_tok()  # eat '['

            e = self.__parse_binary_expr()
            
            if e is None:
                self.__syntax_error()

            if self.__now_tok != ']':
                self.__syntax_error()

            self.__next_tok()  # eat ']'

            return ast.SubscriptExprAST(ca, e, self.__now_ln)
        return ca

    def __parse_low_cell_or_call_expr(self) -> ast.ExprAST:
        if self.__now_tok.ttype == LAP_LLBASKET:
            a = self.__parse_array_expr()

            if a is None:
                self.__syntax_error()

            return a

        if self.__now_tok == '(':
            self.__next_tok()
            e = self.__parse_binary_expr()
            
            if e is None:
                self.__syntax_error()
            
            if self.__now_tok != ')':
                self.__syntax_error()

            self.__next_tok()  # eat ')'
            return e
        
        if self.__now_tok in ('+', '-') and self.__now_tok.ttype != LAP_STRING:
            ntv = self.__now_tok.value

            nt = self.__next_tok()

            if nt.ttype != LAP_NUMBER:
                self.__syntax_error()

            v = self.__now_tok.value

            res = ntv + v

            c = ast.CellAST(res, LAP_NUMBER, self.__now_ln)

            self.__next_tok()  # eat number

            return c

        nt = self.__now_tok

        name = nt.value  # it can be string, number or identifier

        net = self.__next_tok()

        if net.ttype != LAP_SLBASKET:  # is not call expr
            return ast.CellAST(name, nt.ttype, self.__now_ln)

        if net != '(':
            self.__syntax_error()

        # self.__next_tok()  # move to '('

        self.__next_tok()  # eat '('

        al = self.__parse_arg_list()
        if al is None:
            self.__syntax_error()

        return ast.CallExprAST(name, al, self.__now_ln)

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
            rl.append(('^', r))
        return ast.PowerExprAST(left, rl, self.__now_ln)

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
            rl.append(('MOD', r))
        return ast.ModExprAST(left, rl, self.__now_ln)

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

        return ast.MuitDivExprAST(left_op, left, rl, self.__now_ln)

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

        return ast.BinaryExprAST(left_op, left, rl, self.__now_ln)

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

        return ast.PrintExprAST(el, self.__now_ln)

    def __parse_input_expr(self) -> ast.InputExprAST:
        self.__next_tok()  # eat 'INPUT'

        msg = self.__parse_binary_expr()

        if msg is None:
            self.__syntax_error()

        if self.__now_tok != ';':
            return ast.InputExprAST(msg, ast.ValueListAST([], self.__now_ln), self.__now_ln)

        if self.__next_tok().ttype == LAP_IDENTIFIER:
            vl = self.__parse_value_list()
        else:
            vl = ast.ValueListAST([])

        return ast.InputExprAST(msg, vl, self.__now_ln)

    def __parse_define_expr(self) ->ast.DefineExprAST:
            n = self.__now_tok.value
            self.__next_tok()
            self.__next_tok()

            v = self.__parse_binary_expr()

            return ast.DefineExprAST(n, v, self.__now_ln)

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

        return ast.CmpTestAST(left, rl, self.__now_ln)

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

        return ast.AndTestAST(left, rl, self.__now_ln)

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

        return ast.OrTestAST(left, rl, self.__now_ln)

    def __parse_test_expr(self) -> ast.TestExprAST:
        t = self.__parse_or_test_expr()
        
        if t is None:
            self.__syntax_error()

        return ast.TestExprAST(t, self.__now_ln)

    def __parse_if_else_expr(self) -> ast.IfExprAST:
        ln = self.__now_ln
        self.__next_tok()  # eat 'if'

        test = self.__parse_test_expr()

        if self.__now_tok != 'then':
            self.__syntax_error()

        if self.__next_tok().ttype != LAP_ENTER:
            self.__syntax_error()

        if_stmts = []
        el_stmts = []

        in_else = False
        is_elif = False

        now = if_stmts

        while self.__now_tok != 'endif':
            s = self.__parse_stmt()

            # check s
            if isinstance(s, ast.NullLineAST):
                pass
            elif isinstance(s, ast.EOFAST):
                self.__syntax_error("if statement should ends with 'endif'")
            else:
                now.append(s)

            if self.__now_tok == 'else':
                if in_else:
                    self.__syntax_error()
                self.__next_tok()  # eat 'else'

                is_elif = self.__now_tok == 'if'
                
                if self.__now_tok.ttype != LAP_ENTER and not is_elif:
                    self.__syntax_error()

                if not is_elif:
                    self.__next_tok()

                in_else = True
                now = el_stmts

        ifb = ast.BlockExprAST(if_stmts, self.__now_ln)
        elb = ast.BlockExprAST(el_stmts, self.__now_ln)

        self.__next_tok()  # eat 'endif'

        return ast.IfExprAST(test, ifb, elb, ln)

    def __oparse_if_else_expr(self) -> ast.IfExprAST:
        ln = self.__now_ln
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
            return ast.IfExprAST(test, block, 
                    ast.BlockExprAST([], self.__now_ln), self.__now_ln)

        self.__next_tok()  # move to else
        #self.__next_tok()  # eat else

        elseb = self.__parse_block('else', 'endel',
                "else block should starts with 'else'",
                "else block should ends with 'endif'")

        return ast.IfExprAST(test, block, elseb, ln)

    def __parse_while_expr(self) -> ast.WhileExprAST:
        ln = self.__now_ln
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

        return ast.WhileExprAST(test, block,ln)

    def __parse_do_loop_expr(self) -> ast.DoLoopExprAST:
        ln = self.__now_ln
        block = self.__parse_block('do', 'loop', 
                'do loop statement should starts with \'do\'',
                "do loop statement should ends with 'until'")

        if block is None:
            self.__syntax_error()

        if self.__now_tok != 'until':
            self.__syntax_error()

        self.__next_tok()  # eat until

        test = self.__parse_test_expr()

        return ast.DoLoopExprAST(test, block, ln)

    def __parse_func_def_stmt(self) -> ast.FunctionDefineAST:
        ln = self.__now_ln
        self.__next_tok()  # eat 'fun'

        if self.__now_tok.ttype != LAP_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value

        if self.__next_tok() != '(':
            self.__syntax_error()

        self.__next_tok()  # eat '('

        if self.__now_tok == ')':
            arg_list = ast.ArgListAST([], self.__now_ln)  # empty arglist

            self.__next_tok()  # eat ')'
        else:
            arg_list = self.__parse_arg_list()

            for a in arg_list.exp_list:
                if not isinstance(a, ast.CellAST):
                    self.__syntax_error()
                elif a.type != LAP_IDENTIFIER:
                    self.__syntax_error()
        
        self.__level += 1

        block = self.__parse_block('is', 'end')

        self.__level -= 1

        return ast.FunctionDefineAST(name, arg_list, block, ln)

    def __parse_continue_stmt(self) -> ast.ContinueAST:
        if self.__now_tok != 'continue':
            self.__syntax_error()

        self.__next_tok()  # eat 'continue'

        return ast.ContinueAST(self.__now_ln)

    def __parse_break_stmt(self) -> ast.BreakAST:
        if self.__now_tok != 'break':
            self.__syntax_error()

        self.__next_tok()  # eat 'break'

        return ast.BreakAST(self.__now_ln)

    def __parse_return_stmt(self) -> ast.ReturnAST:
        if self.__now_tok != 'return':
            self.__syntax_error()

        self.__next_tok()  # eat 'return'

        expr = self.__parse_binary_expr()

        if expr is None:
            self.__syntax_error()

        return ast.ReturnAST(expr, self.__now_ln)

    def __parse_load_stmt(self) -> ast.LoadAST:
        if self.__now_tok != 'load':
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()  # eat 'load'

        if self.__now_tok.ttype != LAP_STRING:
            self.__syntax_error()

        name = self.__now_tok.value

        self.__next_tok()  # eat name

        return ast.LoadAST(name, ln)

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

        elif nt == 'return':
            if self.__level == 0:
                self.__syntax_error('return outside function')
            a = self.__parse_return_stmt()

        elif nt == 'fun':
            a = self.__parse_func_def_stmt()

        elif nt == 'load':
            a = self.__parse_load_stmt()

        elif nt.ttype not in (LAP_ENTER, LAP_EOF) and \
                nt.value not in (_keywords + limit):
            a = self.__parse_binary_expr()

        elif nt.ttype == LAP_ENTER:
            self.__next_tok()
            return ast.NullLineAST(self.__now_ln)

        elif nt.ttype == LAP_EOF or (
                nt.value in _end_signs and nt.ttype != LAP_STRING):
            return ast.EOFAST(self.__now_ln)

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
            return ast.BlockExprAST([], self.__now_ln)

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

        return ast.BlockExprAST(stmtl, self.__now_ln)

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
