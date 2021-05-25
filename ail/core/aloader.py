# module loader

import os.path

from inspect import isfunction
from os import chdir, getcwd
from traceback import format_exc
from typing import Tuple, Union

from .alex import Lex
from .aparser import Parser
from .acompiler import Compiler
from .astate import MAIN_INTERPRETER_STATE
from .avmsig import WHY_HANDLING_ERR, WHY_ERROR

from . import aobjects as objs, error
from . import shared

_ALLOW_FILE_TYPE = ('ail', 'py', 'ailp')

'''
如果你想要创建一个 AIL 的 Python 模块
请务必在模块中定义一个 '_AIL_NAMESPACE_' 字典
且要在该Python模块中设置 _IS_AIL_MODULE_ = True 字段！
AIL 会加载这个字典，作为 namespace 导入到 AIL 主名称空间中
'''


def is_meta(name):
    return name[:2] == name[-2:] == '__'


def _trim_path(path: str) -> str:
    path = path.replace('/', os.path.sep)
    path = os.path.normpath(path)

    return path


class ModuleLoader:
    def __init__(self):
        self.__loaded = {}
        self.__loading_paths = []
    
    @property
    def __load_path(self):
        return shared.GLOBAL_SHARED_DATA.find_path

    def __search_module(self, name: str) -> str:
        """
        :return: module path if found else None
        """
        maybe_file = ['%s.%s' % (name, x) for x in _ALLOW_FILE_TYPE]

        for mfp in maybe_file:
            for sp in self.__load_path:
                absfp = os.path.abspath(sp)
                jfp = os.path.join(absfp, mfp)
                jfp = _trim_path(jfp)
                if os.path.exists(jfp) and os.path.isfile(jfp):
                    return jfp

        return None

    search_module = __search_module

    def __load_py_namespace(self, pypath, convert: bool = True, pyc_mode=False):
        v = {}

        try:
            cobj = compile(
                    open(pypath, encoding='UTF-8').read(), pypath, 'exec')
            exec(cobj, v)
        except Exception as e:
            excs = format_exc()
            return error.AILRuntimeError(
                '%s' % excs, 'LoadError')

        is_mod = v.get('_IS_AIL_MODULE_', False)
        is_mod = v.get('_AIL_MODULE_', False) if not is_mod else True
        is_pyc_module = v.get('_AIL_PYC_MODULE_', False)
        has_namespace = '_AIL_NAMESPACE_' in v

        if not pyc_mode and is_pyc_module:
            return error.AILRuntimeError(
                'module \'%s\' must load in Python Compatible mode' % pypath,
                'ImportError')

        if not (is_mod or is_pyc_module) or not has_namespace:
            return error.AILRuntimeError(
                '%s is not an AIL MODULE!' % pypath, 'LoadError')

        if '_AIL_NAMESPACE_' in v:
            nsp = v['_AIL_NAMESPACE_']

            # convert all objects to AILObject
            for k, v in nsp.items():
                if is_pyc_module:
                    break

                if not convert:
                    if isfunction(v):
                        nsp[k] = objs.convert_to_ail_object(v)
                    else:
                        nsp[k] = v
                else:
                    nsp[k] = objs.convert_to_ail_object(v)

            return nsp

        return {}

    get_py_namespace = __load_py_namespace

    def __get_type(self, fp: str):
        fn = os.path.split(fp)[-1]
        fns = fn.split('.')

        if len(fns) > 1 and fns[-1] in _ALLOW_FILE_TYPE:
            return fns[-1]

    get_type = __get_type

    def __add_to_loaded(self, module_path: str, namespace: dict):
        self.__check_and_delete_meta(namespace)
        if namespace is not None:
            self.__loaded[module_path] = namespace
        return namespace

    def __check_and_delete_meta(self, namespace: dict):
        del_target = []

        for k in namespace.keys():
            if is_meta(k):
                del_target.append(k)

        for k in del_target:
            del namespace[k]

        return namespace

    def load_namespace(
            self, 
            module_name: str, 
            import_mode: bool = False) -> Union[dict, Tuple]:
        """
        :return: 1 if module not found
                 2 if circular import(or load)
                 3 if error while importing (or loading) a module
                 4 if handing error
        """

        from .avm import Frame

        p = self.__search_module(module_name)

        if p is None:
            return 1, p

        if p in self.__loading_paths:
            return 2, p

        if p in self.__loaded.keys():
            return self.__loaded[p], p

        self.__loading_paths.append(p)
        remove_path = self.__loading_paths.remove
        
        cwd = getcwd()
        module_work_dir = os.path.dirname(p)

        chdir(module_work_dir)

        if self.__get_type(p) in ('py', 'ailp'):
            remove_path(p)
            ns = self.__load_py_namespace(p)
            
            if isinstance(ns, error.AILRuntimeError):
                return ns, p

            ns = self.__add_to_loaded(p, ns)
            chdir(cwd)
            return ns, p

        elif self.__get_type(p) == 'ail':
            source = open(p).read()
            ast = Parser().parse(Lex().lex(source), source, p)
            cobj = Compiler(filename=p, name=p).compile(ast).code_object

            frame = Frame(cobj, cobj.varnames, cobj.consts)

            namespace = dict()
            interpreter = MAIN_INTERPRETER_STATE.global_interpreter
            why = interpreter.exec_for_import(
                    cobj, frame, globals=namespace)

            remove_path(p)
            chdir(cwd)

            if why == WHY_ERROR:
                return 3, p
            elif why == WHY_HANDLING_ERR:
                return 4, p
            
            return self.__add_to_loaded(p, namespace), p

        remove_path(p)
        chdir(cwd)
        return 1, p


MAIN_LOADER = ModuleLoader()
