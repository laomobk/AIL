# virtual machine for AIL

import aobjects as objs
from typing import List
from agc import GC
from astate import InterpreterState
import error
import types
import inspect

import abuiltins

import objects.bool as abool
import objects.integer as aint
import objects.string as astr
import objects.float as afloat
import objects.function as afunc
import objects.wrapper as awrapper
import objects.null as null

import opcodes as opcs

import re

from opcodes import *

__author__ = 'LaomoBK'

# GLOBAL SETTINGS
REFERENCE_LIMIT = 8192
_BYTE_CODE_SIZE = 2
_MAX_RECURSION_DEPTH = 888
_MAX_BREAK_POINT_NUMBER = 50

_BUILTINS = {
    'abs' : objs.ObjectCreater.new_object(afunc.PY_FUNCTION_TYPE, abuiltins.func_abs),
    'ng' : objs.ObjectCreater.new_object(afunc.PY_FUNCTION_TYPE, abuiltins.func_neg),
    'int_input' : objs.ObjectCreater.new_object(afunc.PY_FUNCTION_TYPE, abuiltins.func_int_input),
    '__version__' : objs.ObjectCreater.new_object(astr.STRING_TYPE, "1.0Beta"),
    '__main_version__' : objs.ObjectCreater.new_object(aint.INTEGER_TYPE, 1)
}


class Frame:
    def __init__(self):
        self.code :objs.AILCodeObject = None
        self.stack = []
        self.varnames = []
        self.consts = []
        self.variable = {}
        self.break_stack = []

    def __str__(self):
        return '<Frame object for code object \'%s\'>' % self.code.name

    __repr__ = __str__


class Interpreter:
    def __init__(self):
        self.__now_state = InterpreterState()  # init state
        self.__gc = GC(REFERENCE_LIMIT)  # each interpreter has one GC
        self.__now_state.gc = self.__gc
        self.__frame_stack = self.__now_state.frame_stack

    @property
    def __tof(self) -> Frame:
        return self.__now_state.frame_stack[-1]   \
            if self.__now_state.frame_stack   \
            else None

    @property
    def __tos(self) -> objs.AILObject:
        return self.__tof.stack[-1]   \
            if self.__tof.stack   \
            else None

    @property
    def __stack(self) -> List[objs.AILObject]:
        return self.__tof.stack

    @property
    def __break_stack(self) -> list:
        return self.__tof.break_stack

    def __push_back(self, obj :objs.AILObject):
        self.__stack.append(obj)

    def __pop_top(self) -> objs.AILObject:
        return self.__stack.pop() \
                if self.__stack \
                else self.__raise_error('Pop from empty stack', 'VMError')

    def __push_new_frame(self, cobj :objs.AILCodeObject, frame :Frame=None):
        if len(self.__frame_stack) + 1 > _MAX_RECURSION_DEPTH:
            self.__raise_error('Maximum recursion depth exceeded', 'RecursionError')

        if frame:
            self.__frame_stack.append(frame)
            return

        f = Frame()

        f.consts = cobj.consts
        f.varnames = cobj.varnames

        self.__frame_stack.append(f)

    def __print_err(self, err :error.AILRuntimeError):
        error.print_global_error(err)

    def __check_object(self, aobj :objs.AILObject) -> objs.AILObject:
        if isinstance(aobj, error.AILRuntimeError):
            error.print_global_error(aobj, self.__tof.code.name)
        return aobj

    def __store_var(self, name, value):
        self.__tof.variable[name] = value

    def __raise_error(self, msg :str, err_type :str):
        error.print_global_error(
                error.AILRuntimeError(msg, err_type), self.__tof.code.name)

    def __chref(self, ailobj :objs.AILObject, mode :int):
        '''
        :param mode: 0 -> increase  |  1 -> decrease
        '''

        if isinstance(ailobj, objs.AILObject):
            ailobj.reference -= 1 if mode else -1

            if not ailobj.reference:
                del ailobj

    __incref = lambda self, obj : self.__chref(obj, 0)
    __decref = lambda self, obj : self.__chref(obj, 1)

    def __get_jump(self, jump_to :int, pop :bool, why :int) -> int:
        '''
        :param why: why jump if not will pop. 0 -> False  |  1 -> True
        '''

        tos = self.__tos

        if isinstance(tos, objs.AILObject):
            if tos['__class__'] in (aint.INTEGER_TYPE, abool.BOOL_TYPE):
                if why and tos['__value__'] or not why and not tos['__value__']:
                    if pop:
                        self.__pop_top()
                    return jump_to

        else:
            if why and tos or not why and not tos:
                return jump_to

        return 0

    def __binary_op(self, op :str, pymth :str, ailmth :str, a, b):
        if isinstance(a, objs.AILObject):
            m = a[ailmth]

            if not m:
                self.__raise_error(
                    'Not support \'%s\' with %s and %s' % (op, str(a), str(b)),
                    'TypeError')

            r = m(a, b)
        else:
            if hasattr(a, pymth):
                r = getattr(a, pymth)(b)
            else:
                self.__raise_error(
                        'Not support \'%s\' with %s and %s' % (op, str(a), str(b)), 
                        'TypeError')
        return r

    def __compare(self, a, b, cop :str) -> objs.AILObject:
        if (type(a), type(b)) != (objs.AILObject, objs.AILObject) or \
                (a['__class__'] not in (afloat.FLOAT_TYPE, aint.INTEGER_TYPE) or \
                b['__class__'] not in (afloat.FLOAT_TYPE, aint.INTEGER_TYPE)):
            self.__raise_error(
                'operator \'%s\' can only use between two number' % cop,
                'TypeError'
            )

        av = a['__value__']
        bv = b['__value__']

        if cop in opcs.COMPARE_OPERATORS:
            res = eval('%s %s %s' % (av, cop, bv))
        else:
            self.__raise_error(
                'Unknown compare operator \'%s\'' % cop,
                'VMError'
            )

        return objs.ObjectCreater.new_object(abool.BOOL_TYPE, res)

    def __check_break(self) -> int:
        jump_to = 0
        if self.__break_stack:
            jump_to = self.__break_stack.pop()
        return jump_to

    def __add_break_point(self, cp):
        if len(self.__break_stack) + 1 > _MAX_BREAK_POINT_NUMBER:
            self.__break_stack = []  # reset stack
        self.__break_stack.append(cp)

    def __check_continue(self) -> int:
        jump_to = 0

        if self.__break_stack:
            jump_to = self.__break_stack.pop() - _BYTE_CODE_SIZE
        return jump_to

    def __load_name(self, index :int) -> objs.AILObject:
        for f in self.__frame_stack[::-1]:
            n = self.__tof.varnames[index]

            if n in f.variable.keys():
                return f.variable[n]
        else:
            self.__raise_error('name \'%s\' is not defined' % n, 'NameError')

    def __run_bytecode(self, cobj :objs.AILCodeObject, frame :Frame=None):
        # push a new frame
        self.__push_new_frame(cobj, frame)
        code = cobj.bytecodes

        cp = 0
        jump_to = 0

        while cp < len(code) - 1:  # included argv index
            op = code[cp]
            argv = code[cp + 1]

            # 解释字节码选用类似 ceval.c 的巨型switch做法
            # 虽然可能不太美观，但是能提高运行速度
            # 如果有时间，我会写一个新的（动态获取attr）解释方法
            # 速度可能会慢些

            # print(cp, get_opname(op), self.__tof, self.__stack)

            if op == pop_top:
                tos = self.__pop_top()
                self.__decref(tos)

            elif op == print_value:
                tosl = [self.__pop_top() for _ in range(argv)][::-1]
                
                for tos in tosl:
                    if isinstance(tos, objs.AILObject):
                        tosm = self.__check_object(tos['__str__'](tos))
                    else:
                        tosm = str(tos)

                    print(tosm, end=' ')
                print()

            elif op == input_value:
                vc = argv

                vl = [self.__pop_top() for _ in range(vc)][::-1]
                tos = self.__pop_top()

                if isinstance(tos, objs.AILObject):
                    msg = self.__check_object(tos['__str__'](tos))
                else:
                    msg = str(tos)

                inp = input(msg)

                sip = [astr.convert_to_string(x)
                        for x in re.split(r'\s+', inp) if x]  
                # Remove empty string

                if vl and len(vl) != len(sip):
                    self.__raise_error(
                        'required input value is not enough',
                        'ValueError')

                for k, v in zip(vl, sip):
                    self.__store_var(k, v)

            elif op == store_var:
                v = self.__pop_top()
                n = self.__tof.varnames[argv]

                if v is None:
                    self.__raise_error(
                            'Pop from empty stack', 'VMError')

                if n in self.__tof.variable.keys():
                    self.__decref(self.__tof.variable[n])

                self.__incref(v)

                self.__store_var(n, v)

                self.__push_back(v)

                self.__incref(v)

            elif op == load_const:
                self.__push_back(
                        self.__tof.consts[argv])

            elif op == load_varname:
                self.__push_back(
                    self.__tof.varnames[argv]
                )

            elif op == load_global:
                var = self.__load_name(argv)

                self.__push_back(var)

            elif op == return_value:
                tos = self.__pop_top()

                if len(self.__frame_stack) > 1:
                    self.__frame_stack.pop()

                self.__push_back(tos)

                break  # 结束这个解释循环

            elif op in (setup_doloop, setup_while):
                if op == setup_while:  # setup_while can test TOS
                    tos = self.__pop_top()

                    if tos['__value__'] is not None and not tos['__value__']:
                        jump_to = argv
                    else:
                        self.__add_break_point(argv)
                else:
                    self.__add_break_point(argv)

            elif op == jump_absolute:
                jump_to = argv

            elif op == jump_if_false:
                jump_to = self.__get_jump(argv, False, 0)

            elif op == jump_if_false_or_pop:
                tos = self.__pop_top()

                if isinstance(tos, objs.AILObject):
                    if tos['__value__'] is not None and not tos['__value__']:
                        jump_to = argv
                else:
                    if tos:
                        jump_to = argv

            elif op == jump_if_true_or_pop:
                tos = self.__pop_top()

                if isinstance(tos, objs.AILObject):
                    if tos['__value__'] is not None and tos['__value__']:
                        jump_to = argv
                    elif tos['__value__'] is None:
                        if tos:
                            jump_to = argv
                else:
                    if tos:
                        jump_to = argv

            elif op in (binary_add, binary_div, 
                        binary_mod, binary_muit, 
                        binary_pow, binary_sub):
                op, pym, ailm = {
                    binary_add : ('+', '__add__', '__add__'),
                    binary_div : ('/', '__truediv__', '__div__'),
                    binary_mod : ('mod', '__mod__', '__mod__'),
                    binary_muit : ('*', '__muit__', '__muit__'),
                    binary_pow : ('pow', '__pow__', '__pow__'),
                    binary_sub : ('-', '__sub__', '__sub__')
                }.get(op)

                b = self.__pop_top()
                a = self.__pop_top()

                res = self.__check_object(self.__binary_op(op, pym, ailm, a, b))

                self.__push_back(res)

            elif op == compare_op:
                cop = opcs.COMPARE_OPERATORS[argv]

                b = self.__pop_top()
                a = self.__pop_top()

                self.__push_back(
                    self.__compare(a, b, cop)
                )

            elif op == break_loop:
                jump_to = self.__check_break()

            elif op == continue_loop:
                jump_to = self.__check_continue()

            elif op == call_func:
                argl = [self.__pop_top() for _ in range(argv)]
                func :objs.AILObject = self.__pop_top()

                if isinstance(func, objs.AILObject):  # it should be FUNCTION_TYPE
                    if func['__class__'] == afunc.FUNCTION_TYPE:
                        c :objs.AILCodeObject = func['__code__']

                        if c.argcount != argv:
                            self.__raise_error(
                                '\'%s\' takes %d argument(s), but got %d.' % (c.name, c.argcount, argv),
                                'TypeError'
                            )

                        argd = {k: v for k, v in zip(c.varnames[:argv], argl)}
                        # init new frame
                        f = Frame()
                        f.varnames = c.varnames
                        f.variable = argd
                        f.code = c
                        f.consts = c.consts

                        try:
                            self.__run_bytecode(c, f)
                        except RecursionError as e:
                            self.__raise_error(str(e), 'PythonError')
                    elif func['__class__'] == afunc.PY_FUNCTION_TYPE:
                        pyf = func['__pyfunction__']

                        if not hasattr(pyf, '__call__'):
                            self.__raise_error(
                                '\'%s\' object is not callable' % str(type(pyf))
                            )

                        if not inspect.isbuiltin(pyf):
                            # check arguments
                            fc :types.CodeType = pyf.__code__

                            if fc.co_argcount != argv:
                                self.__raise_error(
                                    'function \'%s\' need %s argument(s)' % fc.co_argcount,
                                    'TypeError'
                                )

                        else:
                            argl = [o['__value__'] for o in argl]
                            # unpack argl for builtin function

                        try:
                            rtn = self.__check_object(pyf(*argl))
                        except Exception as e:
                            self.__raise_error(
                                str(e), 'PythonError'
                            )

                        if not isinstance(rtn, objs.AILObject):

                            target = {
                                str: astr.STRING_TYPE,
                                int: aint.INTEGER_TYPE,
                                float: afloat.FLOAT_TYPE,
                                bool: abool.BOOL_TYPE,
                            }.get(type(rtn), awrapper.WRAPPER_TYPE)

                            if rtn is None:
                                rtn = null.null
                            else:
                                rtn = objs.ObjectCreater.new_object(target, rtn)

                        self.__push_back(rtn)

            elif op == store_function:
                tos = self.__pop_top()

                tosf = objs.ObjectCreater.new_object(
                    afunc.FUNCTION_TYPE, tos, self.__tof.variable, tos.name
                )

                n = self.__tof.varnames[argv]
                self.__store_var(n, tosf)

            if jump_to != cp:
                cp = jump_to
            else:
                cp += _BYTE_CODE_SIZE
                jump_to = cp

    def exec(self, cobj):

        f = Frame()
        f.code = cobj
        f.consts = cobj.consts
        f.varnames = cobj.varnames

        # init namespace
        f.variable = _BUILTINS

        self.__run_bytecode(cobj, f)


if __name__ == '__main__':
    from alex import Lex
    from aparser import Parser
    from acompiler import Compiler
    
    l = Lex('tests/test.ail')
    ts = l.lex()

    t = Parser(ts, 'tests/test.ail').parse()

    co = Compiler(t, filename='<TEST>').compile(t)

    inter = Interpreter()
    inter.exec(co.code_object)
