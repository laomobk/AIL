# virtual machine for AIL

from core import aobjects as objs, abuiltins, error, opcodes as opcs, aloader
from typing import List
from core.agc import GC
from core.astate import MAIN_INTERPRETER_STATE
from core import shared
import types
import inspect

import objects.bool as abool
import objects.integer as aint
import objects.string as astr
import objects.float as afloat
import objects.function as afunc
import objects.wrapper as awrapper
import objects.null as null
import objects.array as array
import objects.struct as struct

from core.modules._fileio import _open
from core.modules._error import (
        make_err_struct_object, throw_error, catch_error,
        print_all_error, _err_to_string)

import re
import copy
import sys

from core.opcodes import *
from core._vmsig import *

from core import corecom as ccom

__author__ = 'LaomoBK'

# GLOBAL SETTINGS
REFERENCE_LIMIT = 8192
_BYTE_CODE_SIZE = 2
_MAX_RECURSION_DEPTH = 888
_MAX_BREAK_POINT_NUMBER = 50

_AIL_VERSION = '1.1 build'

shared.GLOBAL_SHARED_DATA.max_recursion_depth = _MAX_RECURSION_DEPTH

_BUILTINS = {
    'abs' : objs.convert_to_ail_object(abuiltins.func_abs),
    'ng' : objs.convert_to_ail_object(abuiltins.func_neg),
    'int_input' : objs.convert_to_ail_object(abuiltins.func_int_input),
    '__version__' : objs.convert_to_ail_object(_AIL_VERSION),
    '__main_version__' : objs.convert_to_ail_object(1),
    'chr' : objs.convert_to_ail_object(abuiltins.func_chr),
    'ord' : objs.convert_to_ail_object(abuiltins.func_ord),
    'hex' : objs.convert_to_ail_object(abuiltins.func_hex),
    'make_type' : objs.convert_to_ail_object(abuiltins.func_make_type),
    'new' : objs.convert_to_ail_object(abuiltins.new_struct),
    'null' : null.null,
    'true' : objs.convert_to_ail_object(True),
    'false' : objs.convert_to_ail_object(False),
    'len' : objs.convert_to_ail_object(abuiltins.func_len),
    'equal' : objs.convert_to_ail_object(abuiltins.func_equal),
    'type' : objs.convert_to_ail_object(abuiltins.func_type),
    'array' : objs.convert_to_ail_object(abuiltins.func_array),
    'equal_type' : objs.convert_to_ail_object(abuiltins.func_equal_type),
    'isinstance' : objs.convert_to_ail_object(abuiltins.func_isinstance),
    'str' : objs.convert_to_ail_object(abuiltins.func_str),
    'repr' : objs.convert_to_ail_object(abuiltins.func_repr),
    '_get_ccom' : objs.convert_to_ail_object(ccom.get_cc_object),
    'open' : objs.convert_to_ail_object(_open),
    'int' : objs.convert_to_ail_object(abuiltins.func_int)
}


class TempEnvironment:
    __slots__ = ['temp_var']

    def __init__(self):
        self.temp_var = list()

    def __str__(self):
        return '<TEnv(%s) at %s>' % (str(self.temp_var), hex(id(self)))

    __repr__ = __str__


class _ProtectedSignal:
    __slots__ = []


PROTECTED_SIGNAL = _ProtectedSignal()


class Frame:
    def __init__(self, code :objs.AILCodeObject=None, varnames=[],
                 consts=[], globals={}):
        self.code :objs.AILCodeObject = code
        self.stack = []
        self.varnames = varnames
        self.consts = consts
        self.variable = globals
        self.break_stack = []
        self.temp_env_stack = []
        self.try_stack = []

        self._marked_opcounter = 0
        self._latest_call_opcounter = 0

    def __str__(self):
        return '<Frame object for code object \'%s\'>' % self.code.name

    __repr__ = __str__


class Interpreter:
    def __init__(self):
        MAIN_INTERPRETER_STATE.global_interpreters.append(self)
        self.__now_state = MAIN_INTERPRETER_STATE  # init state
        self.__gc = GC(REFERENCE_LIMIT)  # each interpreter has one GC
        self.__now_state.gc = self.__gc
        self.__frame_stack = self.__now_state.frame_stack
        self.__opcounter = 0

        self.__interrupted = False
        self.__interrupt_signal = 0

        self.__can = 1  # 1 -> pass | 0 -> break

        self.__can_update_opc = True

    def __del__(self):
        MAIN_INTERPRETER_STATE.global_interpreters.pop()

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

    @property
    def __temp_env_stack(self) -> list:
        return self.__tof.temp_env_stack

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

    def __print_err(self, err : error.AILRuntimeError):
        error.print_global_error(err)

    def __check_object(self, aobj :objs.AILObject, not_convert=False) -> objs.AILObject:
        if isinstance(aobj, error.AILRuntimeError):
            self.__raise_error(aobj.msg, aobj.err_type)
        if not isinstance(aobj, objs.AILObject) and not not_convert:
            target = {
                str: astr.STRING_TYPE,
                int: aint.INTEGER_TYPE,
                float: afloat.FLOAT_TYPE,
                bool: abool.BOOL_TYPE,
                list: array.ARRAY_TYPE,
            }.get(type(aobj), awrapper.WRAPPER_TYPE)

            if aobj is None:
                aobj = null.null
            else:
                aobj = objs.ObjectCreater.new_object(target, aobj)

        return aobj

    def __store_var(self, name, value):
        if self.__temp_env_stack and name not in self.__tof.variable:
            self.__temp_env_stack[-1].temp_var.append(name)
        self.__tof.variable[name] = value

    def __raise_error(self, msg :str, err_type :str):
        errs = make_err_struct_object(
            error.AILRuntimeError(msg, err_type, self.__tof), self.__tof.code.name, self.__opcounter)

        if err_type not in ('VMError'):
            self.__now_state.err_stack.append(errs)
        else:
            error.print_global_error(
                error.AILRuntimeError(msg, err_type, self.__tof), 
                    '%s +%s' % 
                    (self.__tof.code.name, self.__opcounter))

        self.__now_state.handling_err_stack.append(errs)

        if self.__tof.try_stack:
            to = self.__tof.try_stack.pop()

            self.__opcounter = to

            self.__interrupted = True
            self.__interrupt_signal = MII_DO_JUMP

            return

        for f in self.__frame_stack:
            if f.try_stack:
                break
        else:
            for err in self.__now_state.handling_err_stack[:-1]:
                sys.stderr.write(_err_to_string(err) + '\n')
                sys.stderr.write('\n%s\n\n' %
                      'During handling of the above exception, another exception occurred:')
            sys.stderr.write(_err_to_string(errs) + '\n')
            sys.exit(1)

        # set interrupt signal.
        self.__interrupted = True
        self.__interrupt_signal = MII_ERR_POP_TO_TRY

    def __handle_error(self):
        if self.__tof.try_stack:
            to = self.__tof.try_stack.pop()

            self.__opcounter = to

            self.__interrupted = True
            self.__interrupt_signal = MII_DO_JUMP

        else:
            self.__interrupted = True
            self.__interrupt_signal = MII_ERR_POP_TO_TRY

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
            mb = b[ailmth]

            if m is None or mb is None:
                self.__raise_error(
                    'Not support \'%s\' between %s and %s' % (op, str(a), str(b)),
                    'TypeError')
            
            r = self.__check_object(m(a, b))

        else:
            if hasattr(a, pymth):
                r = getattr(a, pymth)(b)
            else:
                self.__raise_error(
                        'Not support \'%s\' with %s and %s' % (op, str(a), str(b)), 
                        'TypeError')
        return r

    def __compare(self, a, b, cop :str) -> objs.AILObject:
        if not (type(a), type(b)) != (objs.AILObject, objs.AILObject) or \
                (a['__class__'] not in (afloat.FLOAT_TYPE, aint.INTEGER_TYPE) or \
                b['__class__'] not in (afloat.FLOAT_TYPE, aint.INTEGER_TYPE)):

            av = a['__value__']
            bv = b['__value__']

            if cop in opcs.COMPARE_OPERATORS:
                res = eval('%s %s %s' % (av, cop, bv))
            else:
                self.__raise_error(
                    'Unknown compare operator \'%s\'' % cop,
                    'VMError'
                )
        else:
            res = a['__equals__'](a, b)

        return objs.ObjectCreater.new_object(abool.BOOL_TYPE, res)

    def __goto_catch(self):
        to = self.__tof.try_stack[-1]

        self.__opcounter = to

        self.__interrupted = True
        self.__interrupt_signal = MII_DO_JUMP

    def interrupt(self, signal, argv):
        if signal == MII_DO_JUMP:
            self.__opcounter = argv
            self.__interrupted = True
            self.__interrupt_signal = MII_DO_JUMP

    def __bool_test(self, obj):
        if isinstance(obj, objs.AILObject):
            if objs.has_attr(obj, '__value__'):
                return bool(obj['__value__'])
        return bool(obj)

    def __check_break(self) -> int:
        jump_to = 0
        if self.__break_stack:
            jump_to = self.__break_stack.pop()
        return jump_to

    def __add_break_point(self, cp):
        if len(self.__break_stack) + 1 > _MAX_BREAK_POINT_NUMBER:
            self.__break_stack.clear()  # reset stack
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

    def __call_function(self, func, argv, argl):
        self.__tof._marked_opcounter = self.__opcounter

        if isinstance(func, objs.AILObject):  # it should be FUNCTION_TYPE
            if func['__class__'] == afunc.FUNCTION_TYPE:
                c: objs.AILCodeObject = func['__code__']

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
                    if func['__this__'] is not None :
                        this = copy.copy(func['__this__'])
                        this._pthis_ = True  # add _pthis_ attr

                        f.variable['this'] = this  # add this pointer

                        self.__incref(this)
                        self.__incref(this)
                except TypeError:
                    pass

                try:
                    self.__tof._latest_call_opcounter = self.__opcounter

                    why = self.__run_bytecode(c, f)

                    if why == WHY_ERROR:
                        self.__goto_catch()
                    elif why == WHY_HANDLING_ERR:
                        # do nothing
                        pass
                    else:
                        self.__opcounter = self.__tof._latest_call_opcounter
                        # 如无异常，则还原字节码计数器
 
                except RecursionError as e:
                    self.__raise_error(str(e), 'PythonError')
            elif func['__class__'] == afunc.PY_FUNCTION_TYPE:
                pyf = func['__pyfunction__']
                has_this = False

                if func['__this__'] is not None:
                    has_this = True
                    this = copy.copy(func['__this__'])
                    argl.insert(0, this)  # add this to 0
                    argv += 1

                if not hasattr(pyf, '__call__'):
                    self.__raise_error(
                        '\'%s\' object is not callable' % str(type(pyf))
                    )

                if not inspect.isbuiltin(pyf):
                    # check arguments
                    fc: types.CodeType = pyf.__code__

                    fd = pyf.__defaults__
                    fcc = fc.co_argcount
                    fac = fc.co_argcount - (len(fd) if fd is not None else 0)

                    if fac > argv or (argv not in range(fac, fcc + 1)):
                        self.__raise_error(
                            'function \'%s\' need %s positional argument(s)' %
                            (pyf.__name__, fac - (1 if has_this else 0)),
                            'TypeError'
                        )

                else:
                    argl = [o['__value__'] if objs.has_attr(o, '__value__') else o for o in argl]
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
                        list: array.ARRAY_TYPE
                    }.get(type(rtn), awrapper.WRAPPER_TYPE)

                    if rtn is None:
                        rtn = null.null
                    else:
                        rtn = objs.ObjectCreater.new_object(target, rtn)

                self.__push_back(rtn)
            else:
                self.__raise_error(
                    '\'%s\' object is not callable.' % func['__class__'].name, 'TypeError')

    def __return(self):
        tos = self.__pop_top()

        if len(self.__frame_stack) > 1:
            f = self.__frame_stack.pop()
            for o in f.variable.values():
                self.__decref(o)

            self.__push_back(tos)

        else:
            self.__decref(tos)

        self.__can = 0

    def __run_bytecode(self, cobj :objs.AILCodeObject, frame :Frame=None):
        # push a new frame
        self.__push_new_frame(cobj, frame)
        code = cobj.bytecodes

        self.__opcounter = 0
        jump_to = 0

        why = WHY_NORMAL

        try:
            while self.__opcounter < len(code) - 1:  # included argv index
                op = code[self.__opcounter]
                argv = code[self.__opcounter + 1]

                # 解释字节码选用类似 ceval.c 的巨型switch做法
                # 虽然可能不太美观，但是能提高运行速度
                # 如果有时间，我会写一个新的（动态获取attr）解释方法
                # 速度可能会慢些

                # print(cp, get_opname(op), self.__tof, self.__stack)

                # print(self.__opcounter)

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
                    self.__return()

                elif op == setup_for:
                    self.__temp_env_stack.append(TempEnvironment())
                    self.__add_break_point(argv)

                elif op in (setup_doloop, setup_while):
                    self.__add_break_point(argv)

                elif op == clean_for:
                    ts = self.__temp_env_stack.pop()
                    tv = ts.temp_var

                    for vn in tv:
                        del self.__tof.variable[vn]

                    self.__break_stack.pop()

                elif op == clean_loop:
                    self.__break_stack.pop()

                elif op == jump_absolute:
                    jump_to = argv

                elif op == jump_if_false:
                    jump_to = self.__get_jump(argv, False, 0)

                elif op == jump_if_false_or_pop:
                    tos = self.__pop_top()

                    if not self.__bool_test(tos):
                        jump_to = argv

                elif op == jump_if_true_or_pop:
                    tos = self.__pop_top()

                    if self.__bool_test(tos):
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

                elif op == binary_not:
                    o = self.__pop_top()

                    b = not self.__bool_test(o)

                    self.__push_back(
                        objs.ObjectCreater.new_object(abool.BOOL_TYPE, b))

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
                    argl = [self.__pop_top() for _ in range(argv)][::-1]
                    func :objs.AILObject = self.__pop_top()

                    self.__call_function(func, argv, argl)

                elif op == store_function:
                    tos = self.__pop_top()

                    tosf = objs.ObjectCreater.new_object(
                        afunc.FUNCTION_TYPE, tos, self.__tof.variable, tos.name
                    )

                    n = self.__tof.varnames[argv]
                    self.__store_var(n, tosf)

                elif op == build_array:
                    l = [self.__stack.pop() for _ in range(argv)][::-1]

                    o = objs.ObjectCreater.new_object(
                            array.ARRAY_TYPE, l)

                    self.__incref(o)
                    self.__push_back(o)

                elif op == binary_subscr:
                    v = self.__pop_top()
                    l = self.__pop_top()
                    
                    if isinstance(l, objs.AILObject):
                        if l['__getitem__'] is None:
                            self.__raise_error('%s object is not subscriptable' % 
                                    l['__class__'].name, 'TypeError')
                        
                        rtn = self.__check_object(l['__getitem__'](l, v))
                        
                        self.__push_back(rtn)

                elif op == load_module:
                    name = self.__tof.consts[argv]['__value__']

                    v = self.__check_object(aloader.MAIN_LOADER.load_namespace(name), not_convert=True)

                    if v is None:
                        self.__raise_error('No module named \'%s\'' % name, 'LoadError')

                    self.__tof.variable.update(v)

                elif op == store_subscr:
                    i = self.__pop_top()
                    o = self.__pop_top()
                    v = self.__pop_top()

                    if isinstance(o, objs.AILObject):
                        if o['__setitem__'] is None:
                            self.__raise_error('%s object is not subscriptable' %
                                               o['__class__'].name, 'TypeError')

                        self.__check_object(afunc.call(o['__setitem__'], o, i, v))

                    self.__push_back(v)

                elif op == load_attr:
                    o = self.__pop_top()
                    vn = self.__tof.varnames[argv]

                    r = self.__check_object(o['__getattr__'](o, vn))

                    self.__push_back(r)

                elif op == store_attr:
                    o = self.__pop_top()
                    ni = self.__tof.varnames[argv]
                    v = self.__pop_top()

                    self.__check_object(o['__setattr__'](o, ni, v))

                    self.__push_back(v)

                elif op == store_struct:
                    name = self.__pop_top()
                    nl = [self.__pop_top() for _ in range(argv)][::-1]
                    pl = [nl[i - 1] for i in range(len(nl)) if nl[i] == PROTECTED_SIGNAL]
                    nl = [x for x in nl if x != PROTECTED_SIGNAL]

                    o = objs.ObjectCreater.new_object(
                        struct.STRUCT_TYPE, name, nl, pl)

                    self.__store_var(name, o)

                elif op == set_protected:
                    self.__push_back(PROTECTED_SIGNAL)

                elif op == throw_error:
                    self.__tof._marked_opcounter = self.__opcounter
                    msg = str(self.__pop_top())
                    self.__raise_error(msg, 'Throw')

                elif op == setup_try:
                    self.__tof.try_stack.append(argv)

                elif op == setup_catch:
                    name = self.__tof.varnames[argv]
                    self.__temp_env_stack.append(TempEnvironment())

                    err = self.__now_state.err_stack.pop()
                    self.__store_var(name, err) # store this error with 'name'

                elif op == clean_try:
                    self.__tof.try_stack.pop()

                elif op == clean_catch:
                    ts = self.__temp_env_stack.pop()

                    tn = ts.temp_var

                    self.__now_state.handling_err_stack.pop(0)  # queue

                    # self.__tof.try_stack.pop()

                    for n in tn:
                        del self.__tof.variable[n]

                if self.__interrupted:
                    self.__interrupted = False
                    if self.__interrupt_signal == MII_DO_JUMP:
                        jump_to = self.__opcounter
                        continue

                    elif self.__interrupt_signal == MII_ERR_BREAK:
                        why = WHY_ERROR
                        self.__can_update_opc = False

                        break
                    
                    elif self.__interrupt_signal == MII_ERR_POP_TO_TRY:
                        self.__interrupted = True
                        self.__interrupt_signal = MII_ERR_POP_TO_TRY
                        
                        self.__frame_stack.pop()
                        self.__handle_error()

                        why = WHY_HANDLING_ERR
                        break
                
                if not self.__can:
                    self.__can = 1
                    break

                if jump_to != self.__opcounter:
                    self.__opcounter = jump_to
                else: 
                    self.__opcounter += _BYTE_CODE_SIZE
                    jump_to = self.__opcounter

        except (EOFError, KeyboardInterrupt) as e:
            self.__raise_error(str(type(e).__name__), 'RuntimeError')
        return why

    def exec(self, cobj, frame=None):
        if not frame:
            f = Frame()
            f.code = cobj
            f.consts = cobj.consts
            f.varnames = cobj.varnames

            # init namespace
            f.variable = _BUILTINS
        else:
            f = frame

        self.__run_bytecode(cobj, f)


def test_vm():
    from core.alex import Lex
    from core.aparser import Parser
    from core.acompiler import Compiler
    
    l = Lex('tests/test.ail')
    ts = l.lex()

    t = Parser('tests/test.ail').parse(ts)

    co = Compiler(filename='<TEST>').compile(t)

    inter = Interpreter()
    inter.exec(co.code_object)


if __name__ == '__main__':
    test_vm()
