from core.alex import Token, TokenStream, Lex
from core import asts as ast, test_utils
from core.error import error_msg
from core.tokentype import *

__author__ = 'LaomoBK'

_keywords_uc = (
        'PRINT', 'INPUT',
        'IF', 'THEN', 'BEGIN',
        'END', 'WHILE', 'DO',
        'UNTIL', 'LOOP', 'WEND',
        'FUN', 'IS', 'ELSE',  'ENDIF', 'LOAD',
        'STRUCT', 'MOD', 'FOR', 'PROTECTED',
        'ASSERT', 'THROW'
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
    def __init__(self, filename :str):
        self.__filename = filename
        self.__tok_stream = None
        self.__tok_list = None

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
        self.__next_tok()  # eat ')'

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

        while self.__now_tok.ttype == LAP_ENTER or \
                self.__now_tok.value == '\n':  # ignore ENTER
            self.__next_tok()  # eat ENTER

        il = []

        while self.__now_tok.ttype != LAP_LRBASKET:
            eitem = self.__parse_binary_expr()
            
            if eitem is None:
                self.__syntax_error()

            il.append(eitem)

            while self.__now_tok.ttype == LAP_ENTER or \
                    self.__now_tok.value == '\n':  # ignore ENTER
                self.__next_tok()  # eat ENTER

            if self.__now_tok.ttype == LAP_COMMA:        
                self.__next_tok()

            while self.__now_tok.ttype == LAP_ENTER or \
                    self.__now_tok.value == '\n':  # ignore ENTER
                self.__next_tok()  # eat ENTER

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

    def __parse_member_access_expr(self, set_attr=False, try_=False) -> ast.MemberAccessAST:
        left = self.__parse_cell_or_call_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype != LAP_DOT:
            return left

        rl = []

        while self.__now_tok == '.':
            self.__next_tok()  # eat '.'
            ert = self.__parse_cell_or_call_expr()

            if ert is None or type(ert) not in (
                    ast.SubscriptExprAST, ast.CallExprAST, ast.CellAST):
                self.__syntax_error()

            if isinstance(ert, ast.CellAST) and ert.type != LAP_IDENTIFIER:
                self.__syntax_error()

            rl.append(ert)

        if set_attr and type(rl[-1]) not in (ast.SubscriptExprAST, ast.CellAST):
            if try_:
                return None
            self.__syntax_error()

        return ast.MemberAccessAST(left, rl, self.__now_ln)

    def __parse_cell_or_call_expr(self) -> ast.SubscriptExprAST:
        # in fact, it is for subscript

        ca = self.__parse_low_cell_expr()

        left = ca

        while self.__now_tok.ttype in (LAP_MLBASKET, LAP_SLBASKET):
            nt = self.__now_tok.ttype

            if nt == LAP_MLBASKET:
                self.__next_tok()  # eat '['
                if self.__now_tok == ']':
                    self.__syntax_error()

                expr = self.__parse_binary_expr()

                if self.__now_tok != ']':
                    self.__syntax_error()
                self.__next_tok()  # eat ']'

                left = ast.SubscriptExprAST(left, expr, self.__now_ln)

            elif nt == LAP_SLBASKET:
                self.__next_tok()  # eat '('
                if self.__now_tok == ')':
                    argl = ast.ArgListAST([], self.__now_ln)
                    self.__next_tok()  # eat ')'
                else:
                    argl = self.__parse_arg_list()

                left = ast.CallExprAST(left, argl, self.__now_ln)
        return left

    def __parse_low_cell_expr(self) -> ast.ExprAST:
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

        nt = self.__now_tok

        if self.__now_tok.ttype not in (LAP_NUMBER, LAP_STRING, LAP_IDENTIFIER) or \
                nt in _keywords:
            self.__syntax_error()

        name = nt.value  # it can be string, number or identifier

        self.__next_tok()  # eat NAME

        return ast.CellAST(name, nt.ttype, self.__now_ln)

    def __parse_power_expr(self) -> ast.PowerExprAST:
        left = self.__parse_member_access_expr()
        
        if left is None:
            self.__syntax_error()

        if self.__now_tok != '^':
            return left

        rl = []
        
        while self.__now_tok == '^':
            self.__next_tok()
            r = self.__parse_member_access_expr()
            if r is None:
                self.__syntax_error()
            rl.append(('^', r))
        return ast.PowerExprAST(left, rl, self.__now_ln)

    def __parse_mod_expr(self) -> ast.ModExprAST:
        left = self.__parse_power_expr()
        
        if left is None:
            self.__syntax_error()

        if self.__now_tok != 'mod':
            return left

        rl = []
        
        while self.__now_tok == 'mod':
            self.__next_tok()
            r = self.__parse_power_expr()
            if r is None:
                self.__syntax_error()
            rl.append(('mod', r))
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
        # try assign expr
        ntc = self.__tc
        at = self.__parse_assign_expr()

        if at:
            return at

        self.__tc = ntc

        if self.__now_tok.ttype == LAP_ENTER:
            self.__syntax_error()
            
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

    def __parse_assign_expr(self) -> ast.AssignExprAST:
        left = self.__parse_member_access_expr(True, True)

        if self.__now_tok != '=':
            return None

        if type(left) not in (
                ast.CellAST, ast.SubscriptExprAST, ast.MemberAccessAST):
            self.__syntax_error()

        self.__next_tok()  # eat '='

        expr = self.__parse_binary_expr()

        return ast.AssignExprAST(left, expr, self.__now_ln)

    def __parse_assign_expr0(self) ->ast.DefineExprAST:
            n = self.__now_tok.value
            self.__next_tok()
            self.__next_tok()

            v = self.__parse_binary_expr()

            return ast.DefineExprAST(n, v, self.__now_ln)

    def __parse_comp_test_expr(self) -> ast.CmpTestAST:
        if self.__now_tok == '(':
            self.__next_tok()  # eat '('

            expr = self.__parse_test_expr()

            if self.__now_tok != ')':
                self.__syntax_error()

            self.__next_tok()  # eat ')'

            left = expr

        else:
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

    def __parse_not_test_expr(self) -> ast.NotTestAST:
        if self.__now_tok == 'not':
            self.__next_tok()  # eat 'not'
            expr = self.__parse_comp_test_expr()

            return ast.NotTestAST(expr, self.__now_ln)
        return self.__parse_comp_test_expr()

    def __parse_and_test_expr(self) -> ast.AndTestAST:
        left = self.__parse_not_test_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok != 'and':
            return left

        rl = []

        while self.__now_tok == 'and':
            self.__next_tok()   # eat 'and'
            r = self.__parse_not_test_expr()

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

    def __parse_assign_expr_list(self) -> ast.AssignExprListAST:
        f = self.__parse_assign_expr()

        el = [f]

        while self.__now_tok == ',':
            self.__next_tok()  # eat ','
            e = self.__parse_assign_expr()
            if e is None:
                self.__syntax_error()
            el.append(e)

        return ast.AssignExprListAST(el, self.__now_ln)

    def __parse_binary_expr_list(self) -> ast.BinaryExprListAST:
        f = self.__parse_binary_expr()

        el = [f]

        while self.__now_tok == ',':
            self.__next_tok()  # eat ','
            e = self.__parse_binary_expr()
            if e is None:
                self.__syntax_error()
            el.append(e)

        return ast.BinaryExprListAST(el, self.__now_ln)

    def __parse_for_expr(self) -> ast.ForExprAST:
        if self.__now_tok != 'for':
            self.__syntax_error()

        if self.__next_tok() != '(':
            self.__syntax_error()

        self.__next_tok()  # eat '('

        mt = [None, None, None]
        pt = (self.__parse_assign_expr_list,
              self.__parse_test_expr,
              self.__parse_binary_expr_list)
        ct = (ast.AssignExprListAST,
              None,
              ast.BinaryExprListAST)
        dt = (';', ';', ')')

        for i in range(3):
            if self.__now_tok == dt[i]:
                if ct[i] is not None:
                    mt[i] = ct[i]([], self.__now_ln)
                self.__next_tok()
            else:
                mt[i] = pt[i]()

                if self.__now_tok != dt[i]:
                    self.__syntax_error()
                self.__next_tok()

        initl, test, binl = mt

        forb = self.__parse_block()

        return ast.ForExprAST(initl, test, binl, forb, self.__now_ln)

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

    def __parse_struct_def_stmt(self) -> ast.StructDefineAST:
        if self.__now_tok != 'struct':
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()  # eat 'struct'

        if self.__now_tok.ttype != LAP_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value

        if self.__next_tok() != 'is' or \
                self.__next_tok().ttype != LAP_ENTER:
            self.__syntax_error()

        self.__next_tok()  # eat ENTER

        vl = []
        pl = []

        while self.__now_tok.ttype == LAP_ENTER:
            self.__next_tok()

        while self.__now_tok != 'end':
            if self.__now_tok.ttype != LAP_IDENTIFIER:
                self.__syntax_error()
            
            if self.__now_tok == 'protected':
                nt = self.__next_tok()
                if nt.ttype != LAP_IDENTIFIER:
                    self.__syntax_error()
                pl.append(nt.value)

            vl.append(self.__now_tok.value)

            if self.__next_tok().ttype != LAP_ENTER:
                self.__syntax_error()

            self.__next_tok()  # eat ENTER
        
            while self.__now_tok.ttype == LAP_ENTER:
                self.__next_tok()

        if self.__now_tok != 'end':
            self.__syntax_error()

        self.__next_tok()  # eat 'end'

        return ast.StructDefineAST(name, vl, pl, ln)

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

    def __parse_throw_expr(self) -> ast.ThrowExprAST:
        if self.__now_tok != 'throw':
            self.__syntax_error()

        self.__next_tok()  # eat 'throw'

        expr = self.__parse_binary_expr()

        if expr is None or \
                self.__now_tok.ttype != LAP_ENTER:
            self.__syntax_error()
        
        return ast.ThrowExprAST(expr, self.__now_ln)

    def __parse_assert_expr(self) -> ast.AssertExprAST:
        if self.__now_tok != 'assert':
            self.__syntax_error()

        self.__next_tok()  # eat 'assert'

        expr = self.__parse_test_expr()

        if expr is None or \
                self.__now_tok.ttype != LAP_ENTER:
            self.__syntax_error()
        
        return ast.AssertExprAST(expr, self.__now_ln)

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

        elif nt == 'for':
            a = self.__parse_for_expr()

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

        elif nt == 'struct':
            a = self.__parse_struct_def_stmt()

        elif nt == 'assert':
            a = self.__parse_assert_expr()

        elif nt == 'throw':
            a = self.__parse_throw_expr()

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

    def parse(self, ts :TokenStream) -> ast.BlockExprAST:
        self.__tok_stream = ts
        self.__tok_list = ts.token_list

        self.__tc = 0
        self.__level = 0  # level 0

        while self.__now_tok.ttype == LAP_ENTER:  # skip enter at beginning
            self.__next_tok()

        return self.__parse_block('begin', 'end', 
                'A program should starts with \'begin\'',
                "A program should ends with 'end'")

    def test(self, ts):
        return self.parse(ts)


def test_parse():
    import pprint

    l = Lex('tests/test.ail')
    ts = l.lex()

    p = Parser('tests/test.ail')
    t = p.test(ts)
    pt = test_utils.make_ast_tree(t)
    pprint.pprint(pt)


if __name__ == '__main__':
    test_parse()
