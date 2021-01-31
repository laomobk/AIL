# virtual machine for AIL

__author__ = 'LaomoBK'

import copy
import re
import sys
import types
import inspect

from functools import lru_cache
from typing import List

from . import (
    aobjects as objs,
    abuiltins,
    error,
    aopcode as opcs,
    aloader
)

from .aframe import (
        Frame, Block, BLOCK_LOOP, BLOCK_TRY, BLOCK_CATCH, BLOCK_FINALLY
)

from .agc import GC
from .anamespace import Namespace
from .astate import MAIN_INTERPRETER_STATE, NamespaceState
from .astacktrace import StackTrace
from . import shared

from ..objects import (
    string    as astr,
    integer   as aint,
    bool      as abool,
    wrapper   as awrapper,
    float     as afloat,
    complex   as acomplex,
    array     as array,
    map       as amap,
    function  as afunc,
    null      as null,
    namespace,
    module,
    struct,
    fastnum,
)

from .modules._error import (
    make_err_struct_object, throw_error, catch_error,
    print_all_error, _err_to_string, get_err_struct)
from .test_utils import get_opname
from .version import AIL_VERSION

from .aopcode import *
from .avmsig import *

_BUILTINS = abuiltins.BUILTINS
_new_namespace = namespace.new_namespace

# GLOBAL SETTINGS
REFERENCE_LIMIT = 8192
_BYTE_CODE_SIZE = 2
_MAX_RECURSION_DEPTH = 888
_MAX_BREAK_POINT_NUMBER = 50

_AIL_VERSION = AIL_VERSION

shared.GLOBAL_SHARED_DATA.max_recursion_depth = _MAX_RECURSION_DEPTH
sys.setrecursionlimit(_MAX_RECURSION_DEPTH * 3)  
# three times of AIL recursion depth

true = objs.convert_to_ail_object(True)
false = objs.convert_to_ail_object(False)

_obj_type_dict = {
    str: astr.STRING_TYPE,
    int: aint.INTEGER_TYPE,
    float: afloat.FLOAT_TYPE,
    bool: abool.BOOL_TYPE,
    list: array.ARRAY_TYPE,
}

_num_otypes = {aint.INTEGER_TYPE.otype, 
               afloat.FLOAT_TYPE.otype, 
               acomplex.COMPLEX_TYPE.otype}

_binary_op_dict = {
    binary_add: ('+', '__add__', '__add__'),
    binary_div: ('/', '__truediv__', '__div__'),
    binary_mod: ('mod', '__mod__', '__mod__'),
    binary_muit: ('*', '__mul__', '__muit__'),
    binary_pow: ('^', '__pow__', '__pow__'),
    binary_sub: ('-', '__sub__', '__sub__'),
    binary_lshift: ('<<', '__lshift__', '__lshift__'),
    binary_rshift: ('>>', '__rshift__', '__rshift__'),
    binary_and: ('&', '__and__', '__and__'),
    binary_or: ('|', '__or__', '__or__'),
    binary_xor: ('xor', '__xor__', '__xor__'),
}

_binary_compare_op = (
    '__eq__',
    '__ge__',
    '__le__',
    '__gt__',
    '__lt__',
    '__ne__', 
)


class TempEnvironment:
    __slots__ = ['temp_var']

    def __init__(self):
        self.temp_var = list()

    def __str__(self):
        return '<TEnv(%s) at %s>' % (str(self.temp_var), hex(id(self)))

    __repr__ = __str__


class _ProtectedSignal:
    __slots__ = []


class InterpreterContext:
    def __init__(self, interpreter: 'Interpreter'):
        self.now_state = None
        self.opcounter = 0
        self.can = 1
        self.can_update_opc = True
        self.exec_for_module = False
        self.global_frame = None
        self.globals = None

        self.__interpreter = interpreter
        self.__last_ctx = None

    def __enter__(self, *_):
        self.__last_ctx = self.__interpreter.get_context()
        self.__interpreter.set_context(self)

    def __exit__(self, *_):
        self.__interpreter.set_context(self.__last_ctx)


PROTECTED_SIGNAL = _ProtectedSignal()


class Interpreter:
    def __init__(self):
        self.__now_state = MAIN_INTERPRETER_STATE  # init state
        self.__gc = GC(REFERENCE_LIMIT)  # each interpreter has one GC
        self.__now_state.gc = self.__gc
        self.__opcounter = 0

        self.__interrupted = False
        self.__interrupt_signal = 0

        self.__can = 1  # 1 -> pass | 0 -> break

        self.__can_update_opc = True

        self.__exec_for_module = False

        self.__global_frame = None

        self.__return_value = None
        self.__returning = False

        self.__raise_python_error = False
    
    @property
    def __tof(self) -> Frame:
        return MAIN_INTERPRETER_STATE.frame_stack[-1]

    @property
    def __tos(self) -> objs.AILObject:
        return self.__tof.stack[-1]

    @property
    def __frame_stack(self):
        return MAIN_INTERPRETER_STATE.frame_stack

    @property
    def __stack(self) -> List[objs.AILObject]:
        return self.__tof.stack

    @property
    def __break_stack(self) -> list:
        return self.__tof.break_stack

    @property
    def __temp_env_stack(self) -> list:
        return self.__tof.temp_env_stack

    @property
    def __namespace_state(self) -> NamespaceState:
        return MAIN_INTERPRETER_STATE.namespace_state

    @property
    def __block_stack(self) -> List[Block]:
        return self.__tof.block_stack

    def set_raise_python_error(self, b: bool):
        if isinstance(b, bool):
            self.__raise_python_error = b

    def get_context(self) -> InterpreterContext:
        ctx = InterpreterContext(self)
        ctx.can = self.__can
        ctx.can_update_opc = self.__can_update_opc
        ctx.exec_for_module = self.__exec_for_module
        ctx.global_frame = self.__global_frame
        ctx.now_state = self.__now_state
        ctx.opcounter = self.__opcounter
        ctx.globals = self.__namespace_state.ns_global.ns_dict

        return ctx

    def set_context(self, ctx: InterpreterContext):
        self.__can = ctx.can
        self.__can_update_opc = ctx.can_update_opc
        self.__exec_for_module = ctx.exec_for_module
        self.__global_frame = ctx.global_frame
        self.__now_state = ctx.now_state
        self.__opcounter = ctx.opcounter
        self.__namespace_state.ns_global.ns_dict = ctx.globals

    def __set_globals(self, globals: dict):
        self.__namespace_state.ns_global.ns_dict = globals

    def __check_and_get_namespace(self, name: str):
        return None

    def __push_back(self, obj: objs.AILObject):
        self.__stack.append(obj)

    def __pop_top(self) -> objs.AILObject:
        return self.__stack.pop() 

    def __push_block(self, b_type: int, b_handler: int, b_level: int = None):
        if b_level is None:
            b_level = len(self.__stack)
        self.__tof.block_stack.append(Block(b_type, b_handler, b_level))

    def __pop_block(self):
        return self.__tof.block_stack.pop()

    def __push_new_frame(self, cobj: objs.AILCodeObject, frame: Frame = None):
        if len(self.__frame_stack) + 1 > _MAX_RECURSION_DEPTH:
            self.raise_error('Maximum recursion depth exceeded', 'RecursionError')

        if frame:
            self.__now_state.frame_stack.append(frame)
            return

        f = Frame()

        f.consts = cobj.consts
        f.varnames = cobj.varnames

        self.__frame_stack.append(f)

    def __check_object(self, aobj: objs.AILObject, not_convert=False) -> objs.AILObject:
        if isinstance(aobj, error.AILRuntimeError):
            self.raise_error(aobj.msg, aobj.err_type)
        if not isinstance(aobj, objs.AILObject) and not not_convert:
            return objs.convert_to_ail_object(aobj)

        return aobj

    def get_stack_trace(self) -> StackTrace:
        tof = self.__tof
        return StackTrace([copy.copy(f) for f in self.__frame_stack],
                          tof.lineno, tof.code.filename, tof.code.name)

    def __store_var(self, name, value):
        if self.__tof is self.__global_frame:
            self.__namespace_state.ns_global.ns_dict[name] = value
        else:
            if name in self.__tof.code.global_names and \
                    name in self.__tof.code.global_names:
                self.__namespace_state.ns_global.ns_dict[name] = value
            elif name in self.__tof.code.nonlocal_names:
                for outer in self.__tof.closure_outer:
                    if name in outer:
                        outer[name] = value
            else:
                self.__tof.variable[name] = value

    def __delete_name(self, name_index: int):
        name = self.__tof.varnames[name_index]

        if self.__tof is self.__global_frame:
            return self.__namespace_state.ns_global.ns_dict.pop(name, None)
        else:
            if name in self.__tof.code.global_names:
                return self.__namespace_state.ns_global.ns_dict.pop(name, None)
            elif name in self.__tof.code.nonlocal_names:
                del_target_dict = None
                for outer in self.__tof.closure_outer:
                    if name in outer:
                        del_target_dict = outer
                        break
                if del_target_dict is None:
                    return None
                return del_target_dict.pop(name, None)
            else:
                return self.__tof.variable.pop(name, None)

    def _make_runtime_error_obj(self, msg: str, err_type: str):
        return make_err_struct_object(
                error.AILRuntimeError(
                    msg, err_type, self.__tof, self.get_stack_trace()),
                self.__tof.code.name, self.__tof.lineno)

    def _err_reraise(self):
        if len(self.__now_state.handling_err_stack) == 0:
            return
        err = self.__now_state.handling_err_stack.pop()
        self.__now_state.handling_err_stack.clear()
        self.__now_state.err_stack.append(err)

        # switch to ERROR HANDLING mode again
        raise VMInterrupt(MII_ERR_POP_TO_TRY)

    def raise_error(self, msg: str, err_type: str):
        errs = make_err_struct_object(
            error.AILRuntimeError(
                msg, err_type, self.__tof, self.get_stack_trace()),
            self.__tof.code.name, self.__tof.lineno)

        if err_type != 'VMError':
            self.__now_state.err_stack.append(errs)
        else:
            # force terminate.
            self.__now_state.handling_err_stack.extend(self.__now_state.err_stack)
            error.print_exception_for_vm(
                    self.__now_state.handling_err_stack, errs)
            raise VMInterrupt(MII_ERR_BREAK, handle_it=False)

        raise VMInterrupt(MII_ERR_POP_TO_TRY)

    def __handle_error(self) -> bool:
        """
        :return: True if found try block else False
        """
        try_block = None
        # find catch block or finally block
        stack = self.__block_stack
        while stack:
            b = stack.pop()
            if b.type == BLOCK_TRY:
                try_block = b
                break
            elif b.type == BLOCK_FINALLY:
                # assert: if this condition is True, it means no try block.
                self.__push_back(WHY_HANDLING_ERR)
                self.__opcounter = b.handler
                self.__interrupted = True
                self.__interrupt_signal = MII_DO_JUMP
                stack.append(b)  # push block again.
                return 

        if try_block is not None:
            to = try_block.handler
            self.__opcounter = to
            self.__interrupted = True
            self.__interrupt_signal = MII_DO_JUMP
        elif len(self.__frame_stack) > 1:
            self.__interrupted = True
            self.__interrupt_signal = MII_ERR_POP_TO_TRY
        else:
            err = self.__now_state.err_stack.pop()
            self.__now_state.handling_err_stack.extend(self.__now_state.err_stack)
            error.print_exception_for_vm(self.__now_state.handling_err_stack, err)
            self.__stack.clear()
            self.__frame_stack.pop()
            self.__interrupted = True
            self.__interrupt_signal = MII_ERR_BREAK

    def __chref(self, ailobj: objs.AILObject, mode: int):
        """
        :param mode: 0 -> increase  |  1 -> decrease
        """

    def __decref(self, ailobj):
        ailobj.reference -= 1

        if not ailobj.reference:
            del ailobj

    def __incref(self, ailobj):
        ailobj.reference += 1

    def __get_jump(self, jump_to: int, pop: bool, why: int) -> int:
        """
        :param why: why jump if not will pop. 0 -> False  |  1 -> True
        """

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

    def __update_lineno(self):
        ln_index = self.__opcounter // 2
        lno_list = self.__tof.code.lineno_list

        if ln_index < 0 or ln_index >= len(lno_list):
            return

        lno = lno_list[ln_index]

        if lno >= 0:
            self.__tof.lineno = lno
    
    @lru_cache(None)
    def __binary_op(self, op: str, pymth: str, ailmth: str, a, b):
        if isinstance(a, fastnum.FastNumber) and isinstance(b, fastnum.FastNumber):
            op_method = getattr(a._value, pymth, None)

            if op_method:
                return fastnum.FastNumber(op_method(b._value))
            else:
                self.raise_error(
                    'Not support fast numbers \'%s\' between %s and %s' % (
                        op, str(a), str(b)),
                    'TypeError')

        if isinstance(a, objs.AILObject):
            a_cls = a['__class__']
            b_cls = b['__class__']
            
            if a_cls.otype == astr.STRING_TYPE.otype \
                    and b_cls.otype == astr.STRING_TYPE.otype:
                a_val = a['__value__']
                b_val = b['__value__']

                return objs.convert_to_ail_object(a_val + b_val)

            elif a_cls.otype in _num_otypes and b_cls.otype in _num_otypes:
                try:
                    a_val = a['__value__']
                    b_val = b['__value__']
                    op_method = getattr(a_val, pymth, None)

                    if op_method is not None:
                        res = op_method(b_val)
                        if res is not NotImplemented:
                            return objs.convert_to_ail_number(res)

                        # make __rxxx__
                        pymth = pymth[:2] + 'r' + pymth[2:]
                        op_method = getattr(b_val, pymth, None)
                        if op_method is None:
                            self.raise_error(
                                'Not support operator \'%s\' between %s and %s' % (
                                    op, a, b),
                                'TypeError')

                        res = op_method(a_val)
                        if res is NotImplemented:
                            self.raise_error(
                                'Not support operator \'%s\' between %s and %s'
                                        % (op, a, b),
                                    'TypeError')
                        return objs.convert_to_ail_number(res)
                    else:
                        self.raise_error(
                            'Not support operator \'%s\' between %s and %s' % (
                                op, a, b),
                            'TypeError')
                except ZeroDivisionError as e:
                    self.raise_error(
                        str(e), 'ZeroDivisionError'
                    )
                except Exception as e:
                    self.raise_error(
                        str(e), 'PythonMathError'
                    )
            elif a_cls.otype == struct.STRUCT_OBJ_TYPE.otype:
                m = a.members.get(ailmth)
                if m is not None:
                    self.call_function(m, 1, [b])
                    r = self.__pop_top()
                    return r

            m = a[ailmth]
            mb = b[ailmth]

            if m is None or mb is None:
                self.raise_error(
                    'Not support \'%s\' between %s and %s' % (op, str(a), str(b)),
                    'TypeError')
                return

            r = self.__check_object(m(a, b))
        else:
            if hasattr(a, pymth):
                r = getattr(a, pymth)(b)
            else:
                self.raise_error(
                    'Not support \'%s\' with %s and %s' % (op, str(a), str(b)),
                    'TypeError')
                return
        return r

    def __compare(self, a, b, cmp_opm: str, op: str) -> objs.AILObject:
        if type(a) == fastnum.FastNumber and type(b) == fastnum.FastNumber:
            av = a._value
            bv = b._value

            res = getattr(av, cmp_opm)(bv)
            if res is not NotImplemented:
                return true if res else false
            self.raise_error('Not support \'%s\' between %s and %s' % 
                                (op, a, b),
                             'TypeError')
        a_cls = a['__class__']
        b_cls = b['__class__']
        
        if a_cls.otype in _num_otypes and b_cls.otype in _num_otypes:
            a_val = a['__value__']
            b_val = b['__value__']

            res = getattr(a_val, cmp_opm)(b_val)
            if res is not NotImplemented:
                return true if res else false
            self.raise_error('Not support \'%s\' between %s and %s' % 
                                (op, a, b),
                             'TypeError')
        elif a_cls.otype == struct.STRUCT_OBJ_TYPE.otype:
            m = a.members.get(cmp_opm)
            if m is not None:
                self.call_function(m, 1, [b])
                return self.__pop_top()
        else:
            opm = a[cmp_opm]
            if opm is None:    
                self.raise_error('Not support \'%s\' between %s and %s' % 
                                    (op, a, b),
                                 'TypeError')
            res = opm(a, b)

        return true if res else false

    def __check_block(self, block: Block, for_return: bool = False) -> VMInterrupt:
        if block.type == BLOCK_FINALLY:
            self.__opcounter = block.handler
            if for_return:
                self.__push_back(self.__return_value)
                self.__push_back(WHY_RETURN)
            return VMInterrupt(MII_DO_JUMP)
        return None

    def __pop_and_get_block(self, b_type: int) -> Block:
        stack = self.__block_stack
        block = None
        while stack:
            b = stack.pop()
            if b.type == b_type:
                block = b
                break
        return block

    def __goto_catch(self):
        catch_block = self.__pop_and_get_block(BLOCK_TRY)
        if catch_block is None:
            self.raise_error('no block to handle catch', 'VMError')
        self.__opcounter = catch_block.handler

        self.__interrupted = True
        self.__interrupt_signal = MII_DO_JUMP

    def interrupt(self, signal, argv):
        if signal == MII_DO_JUMP:
            self.__opcounter = argv
            self.__interrupted = True
            self.__interrupt_signal = MII_DO_JUMP
    
    @lru_cache(None)
    def __bool_test(self, obj):
        if '__value__' in obj.properties:
            return bool(obj.properties['__value__'])

    def __pop_and_unwind_block(self, why) -> Block:
        stack = self.__block_stack
        b = self.__block_stack[-1]

        if b.type == BLOCK_CATCH:
            self.__now_state.handling_err_stack.pop(0)
        elif b.type == BLOCK_FINALLY:
            if why == WHY_BREAK or why == WHY_CONTINUE:
                for loop_b in stack[::-1]:
                    if loop_b.type == BLOCK_LOOP:
                        break
                self.__push_back(loop_b.handler)
                self.__push_back(why)
                self.__opcounter = b.handler
                raise VMInterrupt(MII_DO_JUMP)

        stack.pop()
        return b

    def __check_break(self) -> int:
        stack = self.__block_stack
        while stack:
            b = self.__pop_and_unwind_block(WHY_BREAK)
            if b.type == BLOCK_LOOP:
                return b.handler
        self.raise_error('no block to handle \'break\'', 'VMError')

    def __add_break_point(self, cp):
        if len(self.__break_stack) + 1 > _MAX_BREAK_POINT_NUMBER:
            self.__break_stack.clear()  # reset stack
        self.__break_stack.append(cp)

    def __check_continue(self) -> int:
        jump_to = 0
        loop_block = None
        stack = self.__block_stack
        while stack:
            b = stack[-1]
            if b.type == BLOCK_LOOP:
                loop_block = b
                break
            self.__pop_and_unwind_block(WHY_CONTINUE)
        else:
            self.raise_error('no block to handle continue', 'VMError')

        if loop_block is not None:
            jump_to = loop_block.handler - _BYTE_CODE_SIZE * 2
        return jump_to

    def __load_name(self, index: int) -> objs.AILObject:
        n = self.__tof.varnames[index]

        v = self.__tof.variable.get(n)
        if v is not None:
            return v
        
        if len(self.__tof.closure_outer) > 0:
            for outer in self.__tof.closure_outer:
                if n in outer:
                    return outer[n]

        ns_state = self.__namespace_state
        for ns in (ns_state.ns_global, ns_state.ns_builtins):
            v = ns.get(n)
            if v is not None:
                return v

        return None

    def call_function(self, func, argv, argl, ex: bool = False):
        self.__tof._marked_opcounter = self.__opcounter

        if isinstance(func, objs.AILObject):  # it should be FUNCTION_TYPE
            if func['__class__'] == afunc.FUNCTION_TYPE:
                c: objs.AILCodeObject = func['__code__']
                var_arg = c.var_arg
                if var_arg is not None:
                    ex = True

                try:
                    if func['__this__'] is not None:
                        this = copy.copy(func['__this__'])
                        this._pthis_ = True  # add _pthis_ attr

                        # now variable 'this' is replace by param 'this'
                        # 2020-10-13
                        # f.variable['this'] = this  # add this pointer

                        argv += 1
                        argl.insert(0, this)
                except TypeError:
                    pass
                
                if (c.argcount != argv and not ex) or (c.argcount > argv and ex):
                    self.raise_error(
                        '\'%s\' takes %d argument(s), but got %d.' % (
                            c.name, c.argcount, argv),
                        'TypeError'
                    )
                
                argd = {k: v for k, v in zip(c.varnames[:c.argcount], argl)}
                if ex:
                    argd[var_arg] = array.convert_to_array(argl[c.argcount:])
                # init new frame
                f = Frame()

                f.varnames = c.varnames
                f.variable = argd
                f.code = c
                f.consts = c.consts

                if c.closure:
                    f.closure_outer = c._closure_outer

                try:
                    self.__tof._latest_call_opcounter = self.__opcounter

                    # now_globals = self.__namespace_state.ns_global.ns_dict
                    
                    with self.get_context():
                        if func['__global_ns__'] is not None:
                            self.__set_globals(func['__global_ns__'])
                        why = self.__run_bytecode(c, f)

                    # self.__set_globals(now_globals)

                    if why == WHY_HANDLING_ERR or why == WHY_ERROR:
                        # do nothing
                        pass
                    else:
                        self.__opcounter = self.__tof._latest_call_opcounter
                        # 如无异常，则还原字节码计数器
                    self.__push_back(self.__return_value)

                except RecursionError as e:
                    self.raise_error(str(e), 'PythonError')
            elif func['__class__'] == afunc.PY_FUNCTION_TYPE:
                pyf = func['__pyfunction__']
                has_this = False

                # arbitrary number of positional arguments
                has_var_arg = pyf.__code__.co_flags & 0x04 == 0x04

                if func['__this__'] is not None:
                    has_this = True
                    this = copy.copy(func['__this__'])
                    argl.insert(0, this)  # add this to 0
                    argv += 1

                if not hasattr(pyf, '__call__'):
                    self.raise_error(
                        '\'%s\' object is not callable' % str(type(pyf)),
                        'TypeError')

                if inspect.isbuiltin(pyf):
                    argl = [o['__value__'] if objs.has_attr(o, '__value__') \
                                else o for o in argl]
                    # unpack argl for builtin function
                try:
                    rtn = self.__check_object(pyf(*argl))
                except Exception as e:
                    if self.__raise_python_error:
                        raise
                    self.raise_error(
                        str(e), 'PythonError'
                    )
                    return

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

                self.__tof.stack.append(rtn)
            elif func['__class__'] == struct.STRUCT_TYPE:
                struct_obj = abuiltins.new_struct(func)
                new_func = struct_obj.members.get('__init__')

                if new_func is not None:
                    self.call_function(
                            new_func, argv, argl, ex)
                self.__tof.stack.append(struct_obj)

            else:
                self.raise_error(
                    '\'%s\' object is not callable.' %
                    func['__class__'].name, 'TypeError')

    def __return(self, set_value: bool = True):
        if set_value:
            self.__return_value = self.__pop_top()
        stack = self.__block_stack
        while stack:
            block = stack[-1]
            interrupt = self.__check_block(block, True)
            if interrupt is not None:
                raise interrupt
            stack.pop()
        raise VMInterrupt(MII_RETURN)

    def __run_bytecode(self, cobj: objs.AILCodeObject, frame: Frame = None):
        self.__push_new_frame(cobj, frame)
        code = cobj.bytecodes

        self.__opcounter = 0
        jump_to = 0

        why = WHY_NORMAL

        try:
            while self.__opcounter < len(code) - 1:  # included argv index
                try:
                    op = code[self.__opcounter]
                    argv = code[self.__opcounter + 1]

                    self.__update_lineno()

                    # 解释字节码选用类似 ceval.c 的巨型switch做法
                    # 虽然可能不太美观，但是能提高运行速度
                    # 如果有时间，我会写一个新的（动态获取attr）解释方法
                    # 速度可能会慢些

                    # print(self.__opcounter, get_opname(op),
                    #       self.__tof, self.__stack, self.__tof.lineno)

                    # print(self.__opcounter, get_opname(op), self.__stack)
                    # print(self.__opcounter, get_opname(op), self.__frame_stack[-1])

                    if op == pop_top:
                        tos = self.__pop_top()

                    elif op == print_value:
                        tosl = [self.__pop_top() for _ in range(argv)][::-1]

                        for tos in tosl:
                            tosm = self.__check_object(
                                    tos['__str__'](tos), not_convert=True)

                            sys.stdout.write(tosm + ' ')
                        sys.stdout.write('\n')

                    elif op == input_value:
                        vc = argv

                        vl = [self.__pop_top() for _ in range(vc)][::-1]
                        tos = self.__pop_top()

                        if isinstance(tos, objs.AILObject):
                            msg = self.__check_object(tos['__str__'](tos))
                        else:
                            msg = str(tos)

                        inp = input(msg)
                        
                        if vc > 1:
                            sip = [astr.convert_to_string(x)
                                   for x in re.split(r'\s+', inp) if x]
                            # Remove empty string
                        else:
                            sip = [astr.convert_to_string(inp)]

                        if vl and len(vl) != len(sip):
                            self.raise_error(
                                'required input value is not enough',
                                'ValueError')
                        else:
                            for k, v in zip(vl, sip):
                                self.__store_var(k, v)

                    elif op == store_var:
                        v = self.__tof.stack.pop()
                        n = self.__tof.varnames[argv]

                        self.__store_var(n, v)
                        self.__tof.stack.append(v)

                    elif op == load_const:
                        self.__tof.stack.append(
                            self.__tof.consts[argv])

                    elif op == load_varname:
                        self.__tof.stack.append(
                            self.__tof.varnames[argv]
                        )

                    elif op == load_variable:
                        var = self.__load_name(argv)
                        if var is None:
                            name = self.__tof.varnames[argv]
                            self.raise_error(
                                'name \'%s\' is not defined' % name, 'NameError')
                        else:
                            self.__push_back(var)

                    elif op == delete_var:
                        v = self.__delete_name(argv)
                        if v is None:
                            self.raise_error(
                                'name \'%s\' is not defined' % name, 'NameError')

                    elif op == load_global:
                        n = self.__tof.varnames[argv]

                        ns = self.__check_and_get_namespace(n)

                        if ns is not None:
                            self.__tof.stack.append(ns)

                        elif len(self.__now_state.frame_stack) == 1:
                            tof = self.__now_state.frame_stack[0]
                            if n in tof.variable:
                                o = tof.variable[n]
                                o.reference += 1
                                tof.stack.append(o)
                            else:
                                self.raise_error(
                                    'name \'%s\' is not defined' % n, 'NameError')

                        else:
                            for f in self.__frame_stack:
                                if n in f.variable:
                                    o = f.variable[n]
                                    o.reference += 1
                                    self.__tof.stack.append(o)

                                    break
                            else:
                                self.raise_error(
                                    'name \'%s\' is not defined' % n, 'NameError')

                    elif op == push_none:
                        self.__push_back(None)

                    elif op == return_value:
                        self.__return()

                    elif op == setup_for:
                        self.__temp_env_stack.append(TempEnvironment())
                        self.__push_block(BLOCK_LOOP, argv)

                    elif op == setup_doloop or op == setup_while:
                        self.__push_block(BLOCK_LOOP, argv)

                    elif op == pop_for:
                        ts = self.__temp_env_stack.pop()
                        tv = ts.temp_var

                        self.__pop_block()

                    elif op == pop_loop:
                        self.__pop_block()

                    elif op == jump_absolute:
                        jump_to = argv

                    elif op == jump_forward:
                        # normally, jump_to equals self.__opcounter
                        jump_to += argv

                    elif op == jump_if_false:
                        jump_to = self.__get_jump(argv, False, 0)

                    elif op == jump_if_false_or_pop:
                        tos = self.__tof.stack.pop()

                        if not self.__bool_test(tos):
                            jump_to = argv
                            self.__tof.stack.append(tos)

                    elif op == jump_if_true_or_pop:
                        tos = self.__tof.stack[-1]

                        if self.__bool_test(tos):
                            jump_to = argv
                        else:
                            self.__tof.stack.pop()

                    elif op == pop_jump_if_false_or_pop:
                        tos = self.__tof.stack.pop()

                        if not self.__bool_test(tos):
                            jump_to = argv

                    elif op == pop_jump_if_true_or_pop:
                        tos = self.__tof.stack.pop()

                        if self.__bool_test(tos):
                            jump_to = argv

                    elif op in BINARY_OPS:
                        op, pym, ailm = _binary_op_dict.get(op)

                        b = self.__pop_top()
                        a = self.__pop_top()

                        res = self.__check_object(
                                self.__binary_op(op, pym, ailm, a, b))

                        self.__tof.stack.append(res)

                    elif op == binary_not:
                        o = self.__pop_top()

                        b = not self.__bool_test(o)

                        self.__tof.stack.append(
                            objs.ObjectCreater.new_object(abool.BOOL_TYPE, b))

                    elif op == compare_op:
                        cmp_opm = _binary_compare_op[argv]
                        op = COMPARE_OPERATORS[argv]

                        b = self.__pop_top()
                        a = self.__pop_top()

                        self.__tof.stack.append(
                            self.__compare(a, b, cmp_opm, op)
                        )

                    elif op == break_loop:
                        jump_to = self.__check_break()

                    elif op == continue_loop:
                        jump_to = self.__check_continue()

                    elif op == call_func:
                        argl = [self.__pop_top() for _ in range(argv)][::-1]
                        func: objs.AILObject = self.__pop_top()

                        self.call_function(func, argv, argl)

                    elif op == call_func_ex:
                        arg_array = self.__pop_top()
                        func = self.__pop_top()
                        arr_list = objs.unpack_ailobj(arg_array)

                        self.call_function(func, len(arr_list), arr_list, ex=True)

                    elif op == make_function:
                        tos = copy.copy(self.__pop_top())  # type: objs.AILCodeObject

                        if tos.closure:
                            tos._closure_outer = []
                            if self.__tof.code.closure:
                                tos._closure_outer.extend(self.__tof.closure_outer.copy())
                            tos._closure_outer.insert(0, self.__tof.variable)

                        tosf = objs.ObjectCreater.new_object(
                            afunc.FUNCTION_TYPE, tos, self.__tof.variable, tos.name
                        )

                        if self.__exec_for_module:
                            tosf['__global_ns__'] = self.__namespace_state.ns_global.ns_dict

                        self.__push_back(tosf)

                    elif op == build_array:
                        l = [self.__stack.pop() for _ in range(argv)][::-1]

                        o = objs.ObjectCreater.new_object(
                            array.ARRAY_TYPE, l)

                        self.__tof.stack.append(o)

                    elif op == build_map:
                        m = dict()

                        for _ in range(argv):
                            v = self.__pop_top()
                            k = self.__pop_top()
                            
                            m[k] = v

                        o = objs.ObjectCreater.new_object(
                            amap.MAP_TYPE, m)

                        self.__push_back(o)

                    elif op == build_const_key_map:
                        m = dict()

                        keys = self.__pop_top()['__value__']
                        # 'keys' is an array object
                        for i in range(argv):
                            value = self.__pop_top()
                            m[keys[i]] = value

                        o = objs.ObjectCreater.new_object(
                            amap.MAP_TYPE, m)

                        self.__push_back(o)

                    elif op == join_array:
                        arr_list = [self.__stack.pop() for _ in range(argv)][::-1]

                        result = []

                        for arr in arr_list:
                            if not objs.compare_type(arr, array.ARRAY_TYPE):
                                self.raise_error(
                                    'argument after \'*\' must an array, but got %s'
                                        % arr['__class__'],
                                    'TypeError'
                                    )
                            temp_list = arr['__value__']
                            result.extend(temp_list)

                        self.__tof.stack.append(
                                array.convert_to_array(result))

                    elif op == binary_subscr:
                        v = self.__pop_top()
                        l = self.__pop_top()

                        if isinstance(l, objs.AILObject):
                            if l['__getitem__'] is None:
                                self.raise_error(
                                        '%s object is not subscriptable' %
                                        l['__class__'].name, 'TypeError')

                            rtn = self.__check_object(l['__getitem__'](l, v))

                            self.__tof.stack.append(rtn)

                    elif op == unary_negative:
                        v = self.__pop_top()

                        if v['__class__'] in (
                                aint.INTEGER_TYPE, afloat.FLOAT_TYPE):
                            vnum = -objs.unpack_ailobj(v)
                            self.__tof.stack.append(
                                    objs.convert_to_ail_object(vnum))

                            self.__decref(v)
                        else:
                            self.raise_error(
                                'cannot do \'-\' for type: %s' % 
                                v['__class__'].name, 'TypeError')

                    elif op == unary_invert:
                        v = self.__pop_top()

                        if v['__class__'] is aint.INTEGER_TYPE:
                            vnum = ~objs.unpack_ailobj(v)
                            self.__tof.stack.append(
                                    objs.convert_to_ail_object(vnum))

                            self.__decref(v)
                        else:
                            self.raise_error(
                                'cannot do \'~\' for type: %s' % 
                                v['__class__'].name, 'TypeError')

                    elif op == unary_inc or op == unary_dec:
                        target_method, op = ('__inc__', '++')  \
                                            if op == unary_inc  \
                                            else ('__dec__', '--')

                        v = self.__pop_top()
                        method = v[target_method]
                        if method is None:
                            self.raise_error(
                                    'Cannot \'%s\' to type %s' % 
                                        (op, v['__class__']),
                                    'TypeError')
                        else:
                            res = self.__check_object(method(v))
                            self.__push_back(res)

                    elif op == load_module:
                        name = self.__tof.consts[argv]['__value__']

                        namespace, _ = aloader.MAIN_LOADER.load_namespace(name)

                        if namespace is None:
                            pass
                        elif namespace == 1:
                            self.raise_error('No module named \'%s\'' % name, 'LoadError')
                        elif namespace == 2:
                            self.raise_error(
                                'Cannot load module \'%s\' ' % name +
                                '(may caused circular load)', 'LoadError')
                        elif namespace == 3:
                            # error while loading this module
                            self.__interrupted = True
                            self.__interrupt_signal = MII_ERR_BREAK
                        else:
                            for name, value in namespace.items():
                                self.__store_var(name, value)

                    elif op == import_name:
                        name = self.__tof.consts[argv]['__value__']

                        namespace, module_path = aloader.MAIN_LOADER.load_namespace(
                            name, True)

                        namespace = self.__check_object(namespace, True)

                        if namespace is None:
                            pass
                        elif namespace == 1:
                            self.raise_error(
                                'No module named \'%s\'' % name, 'ImportError')
                        elif namespace == 2:
                            self.raise_error(
                                'Cannot import module \'%s\' ' % name +
                                '(may caused circular import)', 'ImportError')
                        elif namespace == 3:
                            self.__interrupted = True
                            self.__interrupt_signal = MII_ERR_POP_TO_TRY

                        elif namespace == 4:
                            pass

                        else:
                            module_object = module.new_module_object(
                                name, module_path, namespace)
                            self.__push_back(module_object)

                    elif op == import_from:
                        module_object = self.__tof.stack[-1]
                        name = self.__tof.varnames[argv]

                        ns = module_object.properties['__namespace__']
                        m_name = module_object.properties['__name__']
                        if name in ns:
                            self.__tof.stack.append(ns[name])
                        else:
                            self.raise_error(
                                    'Cannot import \'%s\' from \'%s\'' % (
                                        name, m_name), 
                                    'ImportError')

                    elif op == store_subscr:
                        i = self.__pop_top()
                        o = self.__pop_top()
                        v = self.__pop_top()

                        if isinstance(o, objs.AILObject):
                            if o['__setitem__'] is None:
                                self.raise_error('%s object is not subscriptable' %
                                                 o['__class__'].name, 'TypeError')

                            else:
                                self.__check_object(afunc.call(o['__setitem__'], o, i, v))
                                self.__tof.stack.append(v)

                    elif op == load_attr:
                        o = self.__pop_top()
                        vn = self.__tof.varnames[argv]

                        r = self.__check_object(o['__getattr__'](o, vn))

                        self.__tof.stack.append(r)

                    elif op == store_attr:
                        o = self.__pop_top()
                        ni = self.__tof.varnames[argv]
                        v = self.__pop_top()

                        self.__check_object(o['__setattr__'](o, ni, v))

                        self.__tof.stack.append(v)

                    elif op == store_struct:
                        name = self.__pop_top()
                        nl = [self.__pop_top() for _ in range(argv)][::-1]
                        pl = [nl[i - 1] for i in range(len(nl)) if nl[i] == PROTECTED_SIGNAL]
                        nl = [x for x in nl if x != PROTECTED_SIGNAL]

                        o = objs.ObjectCreater.new_object(
                            struct.STRUCT_TYPE, name, nl, pl)

                        self.__store_var(name, o)

                    elif op == set_protected:
                        self.__tof.stack.append(PROTECTED_SIGNAL)

                    elif op == throw_error:
                        _err = objs.unpack_ailobj(self.__pop_top())
                        e_msg = ''
                        e_type = ''
                        if isinstance(_err, str):
                            e_msg = _err
                            e_type = 'Throw'
                        elif objs.compare_type(_err, struct.STRUCT_OBJ_TYPE):
                            if struct.struct_obj_isinstance(_err, get_err_struct()):
                                e_msg = objs.unpack_ailobj(_err.members['err_msg'])
                                e_type = objs.unpack_ailobj(_err.members['err_type'])
                            else:
                                self.raise_error('needs Error object or string', 'TypeError')
                        elif _err is None:
                            self._err_reraise()
                        else:
                            self.raise_error('needs Error object or string', 'TypeError')
                        self.raise_error(e_msg, e_type)

                    elif op == setup_finally:
                        self.__push_block(BLOCK_FINALLY, argv)

                    elif op == setup_try:
                        self.__push_block(BLOCK_TRY, argv)

                    elif op == setup_catch:
                        name = self.__tof.varnames[argv]
                        self.__temp_env_stack.append(TempEnvironment())

                        self.__push_block(BLOCK_CATCH, -1)

                        err = self.__now_state.err_stack.pop()
                        self.__now_state.err_stack.clear()  # throw away
                        self.__now_state.handling_err_stack.append(err)
                        self.__store_var(name, err)  # store this error with 'name'

                    elif op == pop_try:
                        self.__pop_block()
                    
                    elif op == pop_finally:
                        self.__pop_block()

                    elif op == end_finally:
                        why = self.__pop_top()  # if no why, None will be pushed.

                        if why == WHY_RETURN:
                            self.__return_value = self.__pop_top()
                            self.__return(False)

                        elif why == WHY_HANDLING_ERR:
                            raise VMInterrupt(MII_ERR_POP_TO_TRY)

                        elif why == WHY_CONTINUE or why == WHY_BREAK:
                            goto = self.__pop_top()
                            goto -= _BYTE_CODE_SIZE * 2 * int(why == WHY_CONTINUE)
                            # if is continue, go back one bytecode
                            
                            self.__opcounter = goto
                            raise VMInterrupt(MII_DO_JUMP)

                    elif op == pop_catch:
                        ts = self.__temp_env_stack.pop()

                        tn = ts.temp_var

                        self.__pop_block()

                        self.__now_state.handling_err_stack.pop(0)  # queue

                        # self.__tof.try_stack.pop()

                        for n in tn:
                            del self.__tof.variable[n]

                    elif op == bind_function:
                        target_struct = self.__load_name(argv)
                        if target_struct is None:
                            self.raise_error('can not find bound target', 'NameError')
                        else:
                            func_name = objs.unpack_ailobj(self.__pop_top())
                            bound_function = self.__pop_top()

                            if not objs.compare_type(
                                    bound_function,
                                    afunc.FUNCTION_TYPE, afunc.PY_FUNCTION_TYPE):
                                self.raise_error('require function', 'TypeError')

                            else:
                                if not objs.compare_type(target_struct, struct.STRUCT_TYPE):
                                    self.raise_error(
                                        'function must be bound to a struct type')

                                target_struct['__bind_functions__'][func_name] = \
                                    bound_function
                except VMInterrupt as interrupt:
                    if interrupt.handle_it:
                        self.__interrupted = True
                        signal = interrupt.signal
                        if signal != -1:
                            self.__interrupt_signal = signal

                except KeyboardInterrupt as _:
                    try:
                        self.raise_error('KeyboardInterrupt', 'Interrupt')
                    except VMInterrupt as interrupt:
                        if interrupt.signal != MII_ERR_BREAK:
                            error.print_exception_for_vm(
                                    self.__now_state.handling_err_stack,
                                        make_err_struct_object(
                                            error.AILRuntimeError(
                                                'KeyboardInterrupt',
                                                'Interrupt',
                                                self.__tof,
                                                self.get_stack_trace()),
                                            self.__tof.code.name,
                                            self.__tof.lineno))
                        self.__interrupted = True
                        self.__interrupt_signal = MII_ERR_BREAK

                except error._AILRuntimeError as err:
                    try:
                        self.raise_error(str(err), 'AILRuntimeError')
                    except VMInterrupt as interrupt:
                        self.__interrupted = True
                        self.__interrupt_signal = interrupt.signal

                if self.__interrupted and \
                        self.__interrupt_signal == MII_ERR_POP_TO_TRY:
                    self.__handle_error()

                # handle interruption
                if self.__interrupted:
                    if not self.__can:
                        self.__can = 1
                    self.__interrupted = False
                    if self.__interrupt_signal == MII_DO_JUMP:
                        jump_to = self.__opcounter
                        continue

                    elif self.__interrupt_signal == MII_RETURN:
                        self.__frame_stack.pop()
                        why = WHY_NORMAL
                        break

                    elif self.__interrupt_signal == MII_ERR_BREAK:
                        why = WHY_ERROR
                        self.__can_update_opc = False
                        break
                    
                    elif self.__interrupt_signal == MII_ERR_EXIT:
                        why = WHY_ERR_EXIT
                        self.__can_update_opc = False
                        break

                    elif self.__interrupt_signal == MII_ERR_POP_TO_TRY:
                        self.__interrupted = True
                        self.__interrupt_signal = MII_ERR_POP_TO_TRY
                        self.__frame_stack.pop()
                        self.__can = 0
                        break

                if not self.__can:
                    self.__can = 1
                    break

                if jump_to != self.__opcounter:
                    self.__opcounter = jump_to
                else:
                    self.__opcounter += _BYTE_CODE_SIZE
                    jump_to = self.__opcounter
        except EOFError as e:
            self.raise_error(str(type(e).__name__), 'RuntimeError')
        except Exception as e:
            raise

        return why

    def exec_for_import(self, cobj, frame: Frame, globals: dict = None):
        with self.get_context():
            why = self.exec(cobj, frame, True, globals=globals)

        return why

    def __exec(self, cobj, frame=None,
               exec_for_module=False, globals: dict = None):
        if not frame:
            f = Frame()
            f.code = cobj
            f.consts = cobj.consts
            f.varnames = cobj.varnames
        else:
            f = frame

        # init namespace
        self.__namespace_state.ns_global.ns_dict = dict() \
            if globals is None \
            else globals
        self.__namespace_state.ns_builtins = abuiltins.BUILTINS_NAMESPACE

        f.lineno = cobj.firstlineno

        self.__namespace_state.ns_global.ns_dict['__main__'] = \
            objs.convert_to_ail_object(cobj.is_main)

        self.__global_frame = f

        self.__exec_for_module = exec_for_module

        return self.__run_bytecode(cobj, f)

    def exec(self, cobj, frame=None,
             exec_for_module=False, globals: dict = None):
        with self.get_context():
            return self.__exec(cobj, frame, exec_for_module, globals)


def test_vm():
    import pickle
    from .alex import Lex
    from .aparser import Parser
    from .acompiler import Compiler

    source = open('tests/test.ail').read()

    l = Lex()
    ts = l.lex(source)

    t = Parser().parse(ts, source)

    cbf = Compiler(filename='<TEST>').compile(t)

    co = cbf.code_object

    inter = Interpreter()
    inter.exec(co)


if __name__ == '__main__':
    test_vm()
