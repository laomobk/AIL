# virtual machine for AIL

import aobjects as objs
from typing import List
from agc import GC
from astate import InterpreterState
import threading
import error
from test_utils import get_opname
import objects as aobj

import re

from opcodes import *

# GLOBAL SETTINGS
REFERENCE_LIMIT = 8192


class Frame:
    def __init__(self):
        self.code :objs.AILCodeObject = None
        self.stack = []
        self.varnames = []
        self.consts = []
        self.variable = {}


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

    def __push_back(self, obj :objs.AILObject):
        self.__stack.append(obj)

    def __pop_top(self) -> objs.AILObject:
        return self.__stack.pop() \
                if self.__stack \
                else None

    def __push_new_frame(self, cobj :objs.AILCodeObject):
        f = Frame()

        f.consts = cobj.consts
        f.varnames = cobj.varnames

        self.__frame_stack.append(f)

    def __print_err(self, err :error.AILRuntimeError):
        error.print_global_error(err)

    def __check_object(self, aobj :objs.AILObject) -> objs.AILObject:
        if isinstance(aobj, error.AILRuntimeError):
            error.print_global_error(aobj)
        return aobj

    def __store_var(self, name, value):
        self.__tof.variable[name] = value

    def __raise_error(self, msg :str, err_type :str):
        error.print_global_error(
                error.AILRuntimeError(msg, err_type))

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
            if tos['__class__'] == aobj.integer.INTEGER_TYPE:
                if why and tos['__value__'] or not why and not tos['__value__']:
                    return jump_to

        else:
            if why and tos or not why and not tos:
                return jump_to


        return 0

    def __binary_op(self, op :str, pymth :str, ailmth :str, a, b):
        if isinstance(a, objs.AILObject):
            r = a[ailmth](a, b)
        else:
            if hasattr(a, pymth):
                r = getattr(a, pymth)(b)
            else:
                self.__raise_error(
                        'Not support \'%s\' with %s and %s' % (op, str(a), str(b)), 
                        'TypeError')
        return r

    def __run_bytecode(self, cobj :objs.AILCodeObject):
        # push a new frame
        self.__push_new_frame(cobj)

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

            if op == print_value:
                pc = argv

                tosl = [self.__pop_top() for _ in range(pc)][::-1]
                
                for tos in tosl:
                    if isinstance(tos, objs.AILObject):
                        tosm = self.__check_object(tos['__str__'](tos))
                    else:
                        tosm = str(tos)

            elif op == input_value:
                vc = argv
                tos = self.__pop_top()
                
                vl = [self.__pop_top() for _ in range(vc)][::-1]

                if isinstance(tos, objs.AILObject):
                    msg = self.__check_object(tos['__str__'](tos))
                else:
                    msg = str(tos)

                inp = input(msg)

                sip = [aobj.string.convert_to_string(x)
                        for x in re.split(r'\s+', inp) if x]  
                # Remove empty string

                if len(vl) != len(sip):
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

                self.__incref(v)

                self.__store_var(n, v)

            elif op == load_const:
                self.__push_back(
                        self.__tof.consts[argv])

            elif op == load_global:
                n = self.__tof.varnames[argv]
                self.__push_back(
                        self.__tof.variable[n])

            elif op == return_value:
                tos = self.__pop_top()

                if len(self.__frame_stack) > 1:
                    self.__frame_stack.pop()

                self.__push_back(tos)

            elif op in (setup_doloop, setup_while):
                pass

            elif op == jump_absolute:
                jump_to = argv

            elif op == jump_if_false:
                jump_to = self.__get_jump(argv, False, 0)

            elif op == jump_if_false_or_pop:
                jump_to = self.__get_jump(argv, True, 0)

            elif op == jump_if_true_or_pop:
                jump_to = self.__get_jump(argv, True, 1)

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
            
            if jump_to:
                cp = jump_to
            else:
                cp += 2

    def test_exec(self, cobj):
        self.__run_bytecode(cobj)


if __name__ == '__main__':
    from alex import Lex
    from aparser import Parser
    from acompiler import Compiler
    
    l = Lex('tests/test.ail')
    ts = l.lex()

    t = Parser(ts, 'tests/test.ail').parse()

    co = Compiler(t).compile(t)

    inter = Interpreter()
    inter.test_exec(co.code_object)
