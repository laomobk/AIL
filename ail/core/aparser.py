from os.path import split

from .aconfig import _PACKAGE_INIT_FILENAME
from .alex import Token, TokenStream, Lex
from . import asts as ast, test_utils
from .error import error_msg
from .tokentype import *

__author__ = 'LaomoBK'

_keywords_uc = (
    'PRINT', 'INPUT',
    'IF', 'THEN', 'BEGIN',
    'END', 'WHILE', 'DO',
    'UNTIL', 'LOOP', 'WEND',
    'FUN', 'IS', 'ELSE', 'ENDIF', 'ELIF', 'LOAD', 'IMPORT',
    'STRUCT', 'MOD', 'FOR', 'PROTECTED',
    'ASSERT', 'THROW', 'TRY', 'CATCH', 'FINALLY',
    'XOR', 'MOD',
    'GLOBAL', 'NONLOCAL',
)

_end_signs_uc = ('WEND', 'END', 'ENDIF', 'ELSE', 'ELIF', 'CATCH')

_keywords = tuple([x.lower() for x in _keywords_uc])
_end_signs = tuple([x.lower() for x in _end_signs_uc])

_cmp_op = (
    AIL_EQ, AIL_LARGER, AIL_SMALER,
    AIL_LARGER_EQ, AIL_SMALER_EQ,
    AIL_UEQ
)

_literal_names = ('null', 'true', 'false')

_FROM_MAIN = 0
_FROM_FUNC = 1


class Parser:
    def __init__(self):
        self.__filename = '<NO FILE>'
        self.__source = '\n'
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
        return self.__tok_stream[self.__tc + step]

    def __parse_bin_expr(self) -> ast.AddSubExprAST:
        pass

    @property
    def __now_tok(self) -> Token:
        return self.__tok_stream[self.__tc]

    @property
    def __now_ln(self) -> int:
        try:
            return self.__now_tok.ln
        except AttributeError:
            return -1

    def __tok_is(self, tok: Token, value: str) -> bool:
        return tok.ttype != AIL_STRING and tok.value == value

    def __syntax_error(self, msg=None, ln: int = 0):
        error_msg(
            self.__now_ln if ln <= 0 else ln,
            'SyntaxError%s' % ((': ' if msg else '') + (msg if msg else '')),
            self.__filename, source=self.__source)

    def __parse_arg_item(self) -> ast.ArgItemAST:
        star = False

        if self.__now_tok.ttype == AIL_MUIT:
            self.__next_tok()  # eat '*'
            star = True
        expr = self.__parse_binary_expr()

        return ast.ArgItemAST(expr, star, self.__now_ln)

    def __parse_func_def_arg_list(self) -> ast.ArgListAST:
        ln = self.__now_ln

        alist = []

        while self.__now_tok.ttype != AIL_SRBASKET:
            a = self.__parse_arg_item()
            if not isinstance(a.expr, ast.CellAST) or  \
                    a.expr.type != AIL_IDENTIFIER:
                self.__syntax_error(ln=a.ln)
            alist.append(a)

            if self.__now_tok.ttype == AIL_COMMA:
                self.__next_tok()  # eat ','

            if a.star:
                break

        self.__next_tok()  # eat ')' 

        return ast.ArgListAST(alist, ln)

    def __parse_arg_list(self) -> ast.ArgListAST:
        alist = []

        while self.__now_tok.ttype != AIL_SRBASKET:
            a = self.__parse_arg_item()
            alist.append(a)

            if self.__now_tok.ttype == AIL_COMMA:
                self.__next_tok()  # eat ','

        self.__next_tok()  # eat ')'

        return ast.ArgListAST(alist, self.__now_ln)

    def __parse_value_list(self) -> ast.ValueListAST:
        if self.__now_tok.ttype != AIL_IDENTIFIER:
            return self.__syntax_error()

        ida = self.__now_tok.value
        idl = [ida]

        self.__next_tok()

        while self.__now_tok == ',' and self.__now_tok.ttype != AIL_ENTER:
            self.__next_tok()

            if self.__now_tok.ttype != AIL_IDENTIFIER:
                self.__syntax_error()

            idl.append(self.__now_tok.value)

            self.__next_tok()

        return ast.ValueListAST(idl, self.__now_ln)

    def __parse_item_list(self) -> ast.ItemListAST:
        if self.__now_tok.ttype == AIL_MRBASKET:
            return ast.ItemListAST([], self.__now_ln)

        while self.__now_tok.ttype == AIL_ENTER or \
                self.__now_tok.value == '\n':  # ignore ENTER
            self.__next_tok()  # eat ENTER

        il = []

        while self.__now_tok.ttype != AIL_MRBASKET:
            eitem = self.__parse_binary_expr()

            if eitem is None:
                self.__syntax_error()

            il.append(eitem)

            while self.__now_tok.ttype == AIL_ENTER or \
                    self.__now_tok.value == '\n':  # ignore ENTER
                self.__next_tok()  # eat ENTER

            if self.__now_tok.ttype == AIL_COMMA:
                self.__next_tok()

            while self.__now_tok.ttype == AIL_ENTER or \
                    self.__now_tok.value == '\n':  # ignore ENTER
                self.__next_tok()  # eat ENTER

        return ast.ItemListAST(il, self.__now_ln)

    def __parse_array_expr(self) -> ast.ArrayAST:
        ln = self.__now_ln

        if self.__now_tok.ttype != AIL_MLBASKET:
            self.__syntax_error()

        self.__next_tok()  # eat '['

        if self.__now_tok.ttype == AIL_MRBASKET:
            self.__next_tok()  # eat ']'
            return ast.ArrayAST(ast.ItemListAST([], self.__now_ln), ln)

        items = self.__parse_item_list()

        if self.__now_tok.ttype != AIL_MRBASKET:
            self.__syntax_error()

        self.__next_tok()

        if items is None:
            self.__syntax_error()

        return ast.ArrayAST(items, ln)

    def __parse_member_access_expr(self, 
                                   set_attr=False, 
                                   try_=False) -> ast.MemberAccessAST:
        left = self.__parse_cell_or_call_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype != AIL_DOT:
            return left

        rl = []

        while self.__now_tok == '.':
            self.__next_tok()  # eat '.'
            ert = self.__parse_cell_or_call_expr()

            if ert is None or type(ert) not in (
                    ast.SubscriptExprAST, ast.CallExprAST, ast.CellAST):
                self.__syntax_error()

            if isinstance(ert, ast.CellAST) and ert.type != AIL_IDENTIFIER:
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

        while self.__now_tok.ttype in (AIL_MLBASKET, AIL_SLBASKET):
            nt = self.__now_tok.ttype
            ln = self.__now_ln

            if nt == AIL_MLBASKET:
                self.__next_tok()  # eat '['
                if self.__now_tok == ']':
                    self.__syntax_error()

                expr = self.__parse_binary_expr()

                if self.__now_tok != ']':
                    self.__syntax_error()
                self.__next_tok()  # eat ']'

                left = ast.SubscriptExprAST(left, expr, ln)

            elif nt == AIL_SLBASKET:
                self.__next_tok()  # eat '('
                if self.__now_tok == ')':
                    argl = ast.ArgListAST([], ln)
                    self.__next_tok()  # eat ')'
                else:
                    argl = self.__parse_arg_list()

                left = ast.CallExprAST(left, argl, ln)
        return left

    def __parse_low_cell_expr(self) -> ast.ExprAST:
        ln = self.__now_ln

        if self.__now_tok.ttype == AIL_MLBASKET:
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

        if self.__now_tok.ttype == AIL_ENTER:
            self.__syntax_error(ln=self.__now_ln - 1)

        elif self.__now_tok.ttype not in (
                AIL_NUMBER, AIL_STRING, AIL_IDENTIFIER, AIL_SUB) or \
                    nt in _keywords:
            self.__syntax_error()

        name = nt.value  # it can be sub, string, number or identifier

        self.__next_tok()  # eat NAME

        return ast.CellAST(name, nt.ttype, ln)

    def __parse_unary_expr(self) -> ast.UnaryExprAST:
        if self.__now_tok.ttype in (
                AIL_SUB, AIL_WAVE, AIL_PLUS_PLUS, AIL_SUB_SUB):
            ln = self.__now_ln
            op = self.__now_tok.value
            self.__next_tok()  # eat op

            right = self.__parse_member_access_expr()

            if right is None:
                self.__syntax_error()

            return ast.UnaryExprAST(op, right, ln)

        return self.__parse_member_access_expr()

    def __parse_power_expr(self) -> ast.PowerExprAST:
        left = self.__parse_unary_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok != '^':
            return left

        rl = []

        while self.__now_tok == '^':
            self.__next_tok()
            r = self.__parse_unary_expr()
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

        if self.__now_tok.ttype not in (AIL_MUIT, AIL_DIV):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (AIL_MUIT, AIL_DIV):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_mod_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.MuitDivExprAST(left_op, left, rl, self.__now_ln)

    def __parse_bin_xor_expr(self) -> ast.BinXorExprAST:
        left = self.__parse_bit_shift_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok != 'xor':
            return left

        rl = []

        while self.__now_tok == 'xor':
            self.__next_tok()
            r = self.__parse_bit_shift_expr()
            if r is None:
                self.__syntax_error()
            rl.append(('xor', r))
        return ast.BinXorExprAST(left, rl, self.__now_ln)

    def __parse_binary_expr(self) -> ast.BitOpExprAST:
        expr = self.__parse_assign_expr()

        return expr

    def __parse_bin_op_expr(self) -> ast.BitOpExprAST:
        left = self.__parse_bin_xor_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype not in (AIL_BIN_OR, AIL_BIN_AND):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (AIL_BIN_OR, AIL_BIN_AND):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_bin_xor_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.BitOpExprAST(left_op, left, rl, self.__now_ln)

    def __parse_bit_shift_expr(self) -> ast.BitShiftExprAST:
        left = self.__parse_add_sub_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype not in (AIL_LSHIFT, AIL_RSHIFT):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (AIL_LSHIFT, AIL_RSHIFT):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_add_sub_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.BitShiftExprAST(left_op, left, rl, self.__now_ln)

    def __parse_add_sub_expr(self) -> ast.AddSubExprAST:
        left = self.__parse_muit_div_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype not in (AIL_PLUS, AIL_SUB):
            return left

        left_op = self.__now_tok.value

        rl = []

        while self.__now_tok.ttype in (AIL_PLUS, AIL_SUB):
            r_op = self.__now_tok.value
            self.__next_tok()

            r = self.__parse_muit_div_expr()
            if r is None:
                self.__syntax_error()

            rl.append((r_op, r))

        return ast.AddSubExprAST(left_op, left, rl, self.__now_ln)

    def __parse_print_expr(self) -> ast.PrintExprAST:
        ln = self.__now_ln
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

        return ast.PrintExprAST(el, ln)

    def __parse_input_expr(self) -> ast.InputExprAST:
        self.__next_tok()  # eat 'INPUT'

        msg = self.__parse_binary_expr()

        if msg is None:
            self.__syntax_error()

        if self.__now_tok != ';':
            return ast.InputExprAST(
                msg, ast.ValueListAST([], self.__now_ln), self.__now_ln)

        if self.__next_tok().ttype == AIL_IDENTIFIER:
            vl = self.__parse_value_list()
        else:
            vl = ast.ValueListAST([], self.__now_ln)

        return ast.InputExprAST(msg, vl, self.__now_ln)

    def __parse_assign_expr(self) -> ast.AssignExprAST:
        left = self.__parse_bin_op_expr()

        if left is None:
            self.__syntax_error()

        if self.__now_tok.ttype != AIL_ASSI:
            return left

        # check left is valid or not
        if type(left) not in (ast.MemberAccessAST,
                              ast.CellAST, ast.SubscriptExprAST):
            self.__syntax_error(ln=left.ln)

        # check cell is valid or not
        if isinstance(left, ast.CellAST):
            if left.value in _literal_names:
                self.__syntax_error('cannot assign to %s' % left.value, left.ln)
            elif left.type in (AIL_NUMBER, AIL_STRING):
                self.__syntax_error('cannot assign to literal', left.ln)

        self.__next_tok()
        r = self.__parse_bin_op_expr()
        if r is None:
            self.__syntax_error()

        return ast.AssignExprAST(left, r, self.__now_ln)

    def __parse_assign_expr0(self) -> ast.DefineExprAST:
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
            self.__next_tok()  # eat 'and'
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
            self.__next_tok()  # eat 'or'
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

    def __parse_new_else_elif_block(self, test: ast.TestExprAST,
                                    if_block: ast.BlockExprAST,
                                    else_block: ast.BlockExprAST, ln: int) -> ast.IfExprAST:
        elif_list = []

        if self.__now_tok.value not in ('else', 'elif') :
            return ast.IfExprAST(test, if_block, elif_list, else_block, ln)

        while self.__now_tok.ttype != AIL_EOF:
            if self.__now_tok == 'else':
                self.__next_tok()  # eat 'else'
                else_block = self.__parse_block()
                if else_block is None:
                    self.__syntax_error()

                return ast.IfExprAST(test, if_block, elif_list, else_block, ln)
            elif self.__now_tok == 'elif':
                self.__next_tok()  # eat 'elif'
                elif_test = self.__parse_test_expr()

                if elif_test is None:
                    self.__syntax_error()

                elif_block = self.__parse_block()

                if elif_block is None:
                    self.__syntax_error()

                elif_list.append(
                    ast.IfExprAST(elif_test, elif_block, [], None, ln))

    def __parse_if_else_expr0(self) -> ast.IfExprAST:
        ln = self.__now_ln
        self.__next_tok()  # eat 'if'

        if_test = self.__parse_test_expr()

        if if_test is None:
            self.__syntax_error()

        is_new_block = self.__now_tok.ttype == AIL_LLBASKET

        if self.__now_tok != 'then' and not is_new_block:
            self.__syntax_error()

        if not is_new_block:
            self.__next_tok()  # eat 'then'

        if_block = self.__parse_block(for_if_else=True)
        else_block = ast.BlockExprAST([], self.__now_ln)
        elif_list = []

        if is_new_block:
            return self.__parse_new_else_elif_block(if_test, if_block, else_block, ln)

        while self.__now_tok.ttype != AIL_EOF:
            if self.__now_tok == 'else':
                self.__next_tok()  # eat 'else'
                else_block = self.__parse_block(for_if_else=True)

                if else_block is None:
                    self.__syntax_error()

                if self.__now_tok == 'endif':
                    self.__next_tok()  # eat 'endif'
                    return ast.IfExprAST(
                        if_test, if_block, elif_list, else_block, ln)
                else:
                    self.__syntax_error()

            elif self.__now_tok == 'elif':
                self.__next_tok()  # eat 'elif'
                elif_test = self.__parse_test_expr()

                if elif_test is None:
                    self.__syntax_error()

                elif_block = self.__parse_block(for_if_else=True)

                if elif_block is None:
                    self.__syntax_error()

                elif_list.append(
                    ast.IfExprAST(elif_test, elif_block, [], None, ln))

            elif self.__now_tok == 'endif':
                self.__next_tok()  # eat 'endif'
                return ast.IfExprAST(
                    if_test, if_block, elif_list, else_block, ln)

            else:
                self.__syntax_error()

    def __parse_if_else_expr(self) -> ast.IfExprAST:
        base_tree = self.__parse_if_else_expr0()

        if len(base_tree.elif_list) == 0:
            return base_tree

        elif_list = base_tree.elif_list

        last_if_else_block = elif_list.pop()
        last_if_else_block.else_block = base_tree.else_block
        base_tree.else_block = None

        for elif_block in elif_list[::-1]:
            elif_block.else_block = ast.BlockExprAST([last_if_else_block], self.__now_ln)
            last_if_else_block = elif_block

        base_tree.else_block = ast.BlockExprAST([last_if_else_block], self.__now_ln)
        base_tree.elif_list = []

        return base_tree

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

        if self.__now_tok.ttype != AIL_ENTER:
            self.__syntax_error()

        return ast.WhileExprAST(test, block, ln)

    def __parse_assign_expr_list(self) -> ast.AssignExprListAST:
        f = self.__parse_assign_expr()
        if not isinstance(f, ast.AssignExprAST):
            self.__syntax_error()

        el = [f]

        while self.__now_tok == ',':
            self.__next_tok()  # eat ','
            e = self.__parse_assign_expr()
            if not isinstance(e, ast.AssignExprAST):
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

        new_block_style = False

        if self.__peek(1).ttype != AIL_LLBASKET:
            block = self.__parse_block('do', 'loop',
                                       'do loop statement should starts with \'do\'',
                                       "do loop statement should ends with 'until'")
        else:
            new_block_style = True
            self.__next_tok()  # eat 'do'
            block = self.__parse_block()

        if block is None:
            self.__syntax_error()

        if new_block_style:
            if self.__now_tok != 'loop':
                self.__syntax_error()
            self.__next_tok()  # eat 'loop'

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

        if self.__now_tok.ttype != AIL_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value
        self.__next_tok()  # eat name

        new_block_style = False

        start_tok = 'is'
        end_tok = 'end'

        if self.__now_tok.ttype == AIL_LLBASKET:
            start_tok = '{'
            end_tok = '}'
            new_block_style = True
        
        if self.__now_tok != start_tok or \
                self.__next_tok().ttype != AIL_ENTER:
            if not new_block_style:
                self.__syntax_error()
        
        if self.__now_tok.ttype == AIL_ENTER:
            self.__next_tok()  # eat ENTER

        vl = []
        pl = []

        while self.__now_tok.ttype == AIL_ENTER:
            self.__next_tok()

        while self.__now_tok != end_tok:
            if self.__now_tok.ttype != AIL_IDENTIFIER:
                self.__syntax_error()

            if self.__now_tok == 'protected':
                nt = self.__next_tok()
                if nt.ttype != AIL_IDENTIFIER:
                    self.__syntax_error()
                pl.append(nt.value)

            vl.append(self.__now_tok.value)

            if self.__next_tok().ttype != AIL_ENTER:
                self.__syntax_error()

            self.__next_tok()  # eat ENTER

            while self.__now_tok.ttype == AIL_ENTER:
                self.__next_tok()

        if self.__now_tok != end_tok:
            self.__syntax_error()

        self.__next_tok()  # eat end_tok

        return ast.StructDefineAST(name, vl, pl, ln)

    def __parse_func_def_with_decorator_stmt(self, 
            parsed: list = None) -> ast.FunctionDefineAST:
        ln = self.__now_ln
        self.__next_tok()  # eat '@'

        if parsed is None:
            parsed = list()

        decorator = self.__parse_member_access_expr()

        parsed.append(decorator)

        if self.__now_tok.ttype != AIL_ENTER:
            self.__syntax_error()

        self.__next_tok()  # eat enter

        if self.__now_tok == '@':
            return self.__parse_func_def_with_decorator_stmt(parsed)
        elif self.__now_tok == 'fun':
            func = self.__parse_func_def_stmt()
            func.decorator.extend(parsed)

            return func
        else:
            self.__syntax_error()


    def __parse_func_def_stmt(self) -> ast.FunctionDefineAST:
        ln = self.__now_ln
        self.__next_tok()  # eat 'fun'

        bindto = None

        if self.__now_tok == '(':
            if self.__next_tok().ttype != AIL_IDENTIFIER:
                self.__syntax_error()
            bindto = self.__now_tok.value

            if self.__next_tok() != ')':
                self.__syntax_error()
            self.__next_tok()

        if self.__now_tok.ttype != AIL_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value

        if self.__next_tok() != '(':
            self.__syntax_error()

        self.__next_tok()  # eat '('

        if self.__now_tok == ')':
            arg_list = ast.ArgListAST([], self.__now_ln)  # empty arglist

            self.__next_tok()  # eat ')'
        else:
            arg_list = self.__parse_func_def_arg_list()

        self.__level += 1

        # for new function syntax (':' instead of 'is')
        if self.__now_tok.ttype == AIL_COLON:
            self.__now_tok.ttype = AIL_IDENTIFIER
            self.__now_tok.value = 'is'

        block = self.__parse_block('is', 'end',
                                   start_msg=
                                   'function body should starts with \'is\' or \':\'')

        self.__level -= 1

        return ast.FunctionDefineAST(name, arg_list, block, bindto, ln)

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

    def __parse_global_stmt(self) -> ast.GlobalStmtAST:
        if self.__now_tok != 'global':
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()  # eat 'global'

        if self.__now_tok.ttype != AIL_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value

        self.__next_tok()  # eat name

        return ast.GlobalStmtAST(name, ln)

    def __parse_nonlocal_stmt(self) -> ast.NonlocalStmtAST:
        if self.__now_tok != 'nonlocal':
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()  # eat 'nonlocal'

        if self.__now_tok.ttype != AIL_IDENTIFIER:
            self.__syntax_error()

        name = self.__now_tok.value 

        self.__next_tok()  # eat name

        return ast.NonlocalStmtAST(name, ln)

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

        ln = self.__now_ln

        self.__next_tok()  # eat 'throw'

        expr = self.__parse_binary_expr()

        if expr is None or \
                self.__now_tok.ttype != AIL_ENTER:
            self.__syntax_error()

        return ast.ThrowExprAST(expr, ln)

    def __parse_assert_expr(self) -> ast.AssertExprAST:
        if self.__now_tok != 'assert':
            self.__syntax_error()

        self.__next_tok()  # eat 'assert'

        expr = self.__parse_test_expr()

        if expr is None or \
                self.__now_tok.ttype != AIL_ENTER:
            self.__syntax_error()

        return ast.AssertExprAST(expr, self.__now_ln)

    def __parse_import_stmt(self) -> ast.ImportAST:
        if self.__now_tok != 'import':
            self.__syntax_error()

        ln = self.__now_ln
        alias = None
        is_dir = False

        self.__next_tok()  # eat 'import'

        if self.__now_tok.ttype == AIL_IDENTIFIER:
            alias = self.__now_tok.value
            self.__next_tok()  # eat name

        if self.__now_tok.ttype != AIL_STRING:
            self.__syntax_error()

        path = self.__now_tok.value
        path = path.replace('\\', '/')
        directory, target = split(path)

        if target == '':
            directory, target = split(directory)  # directory name
            is_dir = True

        if target == '':
            self.__syntax_error('Cannot import a package in current directory.')

        if is_dir:
            if directory == '':
                directory = '.'

            path = '/'.join((directory, target, _PACKAGE_INIT_FILENAME))
            alias = target

        if alias is None:
            name = target
        else:
            name = alias

        self.__next_tok()  # eat path

        return ast.ImportAST(path, name, ln)

    def __parse_load_stmt(self) -> ast.LoadAST:
        if self.__now_tok != 'load':
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()  # eat 'load'

        if self.__now_tok.ttype != AIL_STRING:
            self.__syntax_error()

        name = self.__now_tok.value

        self.__next_tok()  # eat path

        return ast.LoadAST(name, ln)

    def __parse_new_catch_finally_body(self,
            try_block: ast.BlockExprAST) -> ast.TryCatchExprAST:

        has_catch_block = True
        ln = self.__now_ln
        
        if self.__now_tok != 'catch':
            has_catch_block = False
            catch_block = ast.BlockExprAST([], self.__now_ln)
            cname = None
        else:
            
            self.__next_tok()  # eat 'catch'
            
            if self.__now_tok.ttype != AIL_IDENTIFIER:
                self.__syntax_error('require name')

            cname = self.__now_tok.value

            self.__next_tok()  # eat NAME

            catch_block = self.__parse_block()
            if catch_block is None:
                self.__syntax_error()

        if self.__now_tok != 'finally':
            if not has_catch_block:
                self.__syntax_error()

            return ast.TryCatchExprAST(
                    try_block, catch_block, 
                    ast.BlockExprAST([], self.__now_ln), cname, ln)

        self.__next_tok()  # eat 'finally'

        finally_block = self.__parse_block()

        return ast.TryCatchExprAST(
                try_block, catch_block, finally_block, cname, ln)

    def __parse_try_catch_expr(self) -> ast.TryCatchExprAST:
        if self.__now_tok != 'try':
            self.__syntax_error()

        new_block_style = False

        if self.__peek(1).ttype == AIL_LLBASKET:
            new_block_style = True
            self.__next_tok()  # eat '{'

        try_b = self.__parse_block(start='try', end='catch')

        if new_block_style:
            return self.__parse_new_catch_finally_body(try_b)

        if new_block_style:
            self.__next_tok()  # eat 'catch'

        if try_b is None or self.__now_tok.ttype != AIL_IDENTIFIER:
            self.__syntax_error()

        cname = self.__now_tok.value

        self.__next_tok()  # eat NAME

        if self.__now_tok != 'then' or self.__next_tok().ttype != AIL_ENTER:
            self.__syntax_error()

        self.__next_tok()  # eat ENTER

        catch_sl = []
        finally_sl = []

        now = catch_sl
        in_finally = False

        while self.__now_tok != 'end':
            if self.__now_tok == 'finally':
                if in_finally:
                    self.__syntax_error()

                in_finally = True

                if self.__next_tok().ttype != AIL_ENTER:
                    self.__syntax_error()

                self.__next_tok()  # eat ENTER

                now = finally_sl

            if self.__now_tok == 'end':
                break

            s = self.__parse_stmt()

            if isinstance(s, ast.NullLineAST):
                pass
            elif isinstance(s, ast.EOFAST):
                self.__syntax_error("try statement should ends with 'end'")
            else:
                now.append(s)

        cab = ast.BlockExprAST(catch_sl, self.__now_ln)
        fnb = ast.BlockExprAST(finally_sl, self.__now_ln)

        self.__next_tok()  # eat 'end'

        return ast.TryCatchExprAST(try_b, cab, fnb, cname, self.__now_ln)

    def __parse_stmt(self, limit: tuple = ()) -> ast.ExprAST:
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

        elif nt == 'nonlocal':
            if self.__level == 0:
                self.__syntax_error('nonlocal declaration outside function')
            a = self.__parse_nonlocal_stmt()

        elif nt == 'global':
            if self.__level == 0:
                self.__syntax_error('global declaration outside function')
            a = self.__parse_global_stmt()

        elif nt == 'break':
            a = self.__parse_break_stmt()

        elif nt == 'return':
            if self.__level == 0:
                self.__syntax_error('return outside function')
            a = self.__parse_return_stmt()

        elif nt == 'fun':
            a = self.__parse_func_def_stmt()

        elif nt == '@':
            a = self.__parse_func_def_with_decorator_stmt()

        elif nt == 'load':
            a = self.__parse_load_stmt()

        elif nt == 'struct':
            a = self.__parse_struct_def_stmt()

        elif nt == 'assert':
            a = self.__parse_assert_expr()

        elif nt == 'throw':
            a = self.__parse_throw_expr()

        elif nt == 'try':
            a = self.__parse_try_catch_expr()

        elif nt == 'import':
            a = self.__parse_import_stmt()

        elif nt.ttype not in (AIL_ENTER, AIL_EOF) and \
                nt.value not in (_keywords + limit):
            a = self.__parse_binary_expr()

        elif nt.ttype == AIL_ENTER:
            self.__next_tok()
            return ast.NullLineAST(self.__now_ln)

        elif nt.ttype == AIL_EOF or (
                nt.value in _end_signs and nt.ttype != AIL_STRING):
            return ast.EOFAST(self.__now_ln)

        else:
            self.__syntax_error()

        if self.__now_tok.ttype != AIL_ENTER:  
            # a stmt should be end of ENTER
            self.__syntax_error()

        self.__next_tok()  # eat enter

        return a

    def __parse_new_block(self) -> ast.BlockExprAST:
        if self.__now_tok.ttype != AIL_LLBASKET:
            self.__syntax_error()

        ln = self.__now_ln

        self.__next_tok()

        stmt_list = []

        while self.__now_tok.ttype != AIL_LRBASKET:

            s = self.__parse_stmt()

            if s is None:
                self.__syntax_error()

            if not isinstance(s, ast.NullLineAST):
                stmt_list.append(s)

            if isinstance(s, ast.EOFAST):
                self.__syntax_error('block should ends with \'}\'')

        self.__next_tok()  # eat '}'

        return ast.BlockExprAST(stmt_list, ln)

    def __parse_block(self, start='then', end='end',
                      start_msg: str = None, end_msg: str = None,
                      start_enter=True, for_if_else: bool = False, 
                      for_program: bool = False) -> ast.BlockExprAST:
        if self.__now_tok.ttype == AIL_LLBASKET:
            return self.__parse_new_block()

        ln = self.__now_ln

        if for_if_else:
            if self.__now_tok.ttype != AIL_ENTER:
                self.__syntax_error()

            self.__next_tok()  # eat enter

            if self.__now_tok in ('else', 'elif', 'endif'):
                # not eat, leave to if_else parse
                return ast.BlockExprAST([], ln)

        elif for_program:
            if self.__now_tok == start:
                self.__next_tok()
        else:
            if self.__now_tok != start:
                self.__syntax_error(start_msg)

            if start_enter and self.__next_tok().ttype != AIL_ENTER:
                self.__syntax_error()

            self.__next_tok()  # eat enter

            if self.__now_tok == end:  # empty block
                self.__next_tok()
                return ast.BlockExprAST([], ln)

        first = self.__parse_stmt((start, end))

        if first is None:
            self.__syntax_error()

        elif isinstance(first, ast.EOFAST):
            self.__syntax_error(end_msg)

        stmtl = []

        if not isinstance(first, ast.NullLineAST):
            stmtl.append(first)

        while self.__now_tok != end:
            if for_if_else and self.__now_tok.value in (
                    'elif', 'else', 'endif'):
                return ast.BlockExprAST(stmtl, ln)

            s = self.__parse_stmt((start, end))

            if s is None:
                self.__syntax_error()

            if isinstance(s, ast.EOFAST):
                if for_program:
                    break
                self.__syntax_error(end_msg)

            if not isinstance(s, ast.NullLineAST):
                stmtl.append(s)

        self.__next_tok()  # eat end

        return ast.BlockExprAST(stmtl, ln)

    def parse(self, ts: TokenStream, 
              source: str, filename: str) -> ast.BlockExprAST:
        self.__init__()
        self.__tok_stream = ts
        self.__filename = filename
        self.__source = source
        self.__tok_list = ts.token_list

        self.__tc = 0
        self.__level = 0  # level 0

        if len(ts.token_list) == 0:
            return ast.BlockExprAST([], 0)

        while self.__now_tok.ttype == AIL_ENTER:  # skip enter at beginning
            self.__next_tok()

        return self.__parse_block('begin', 'end',
                                  'A program should starts with \'begin\'',
                                  "A program should ends with 'end'",
                                  for_program=True)

    def test(self, ts, source):
        return self.parse(ts, source, '<test>')


def test_parse():
    import pprint

    source = open('./tests/test.ail').read()
    l = Lex()
    ts = l.lex(source)

    p = Parser()
    t = p.test(ts, source)
    pt = test_utils.make_ast_tree(t)
    pprint.pprint(pt)


if __name__ == '__main__':
    test_parse()
