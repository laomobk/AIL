# module loader

import os.path

from os import chdir, getcwd
from traceback import format_exc

from .abuiltins import BUILTINS
from .alex import Lex
from .aparser import Parser
from .acompiler import Compiler
from .astate import MAIN_INTERPRETER_STATE
from .avmsig import WHY_HANDLING_ERR, WHY_ERROR

from . import aobjects as objs, error
from . import shared

_ALLOW_FILE_TYPE = ('ail', 'py')

'''
如果你想要创建一个 AIL 的 Python 模块
请务必在模块中定义一个 '_AIL_NAMESPACE_' 字典
且要在该Python模块中设置 _IS_AIL_MODULE_ = True 字段！
AIL 会加载这个字典，作为 namespace 导入到 AIL 主名称空间中
'''


def _trim_path(path: str) -> str:
    path = path.replace('/', os.path.sep)
    path = os.path.normpath(path)

    return path


class ModuleLoader:
    def __init__(self, paths: list):
        self.__load_path = paths
        self.__loaded = {}
        self.__loading_paths = []

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

    def __load_py_namespace(self, pypath):
        v = {}

        try:
            cobj = compile(open(pypath, encoding='UTF-8').read(), pypath, 'exec')
            exec(cobj, v)
        except Exception as e:
            excs = format_exc()
            return error.AILRuntimeError(
                '%s' % excs, 'LoadError')

        is_mod = v.get('_IS_AIL_MODULE_', None)

        if is_mod is not True:
            return error.AILRuntimeError(
                '%s is not an AIL MODULE!' % pypath, 'LoadError')

        if '_AIL_NAMESPACE_' in v:
            nsp = v['_AIL_NAMESPACE_']

            # convert all objects to AILObject
            for k, v in nsp.items():
                nsp[k] = objs.convert_to_ail_object(v)

            return nsp

        return {}

    def __get_type(self, fp: str):
        fn = os.path.split(fp)[-1]
        fns = fn.split('.')

        if len(fns) > 1 and fns[-1] in _ALLOW_FILE_TYPE:
            return fns[-1]

    def __add_to_loaded(self, module_path: str, namespace: dict):
        if namespace is not None:
            self.__loaded[module_path] = namespace
        return namespace

    def load_namespace(
            self, module_name: str, import_mode: bool = False) -> dict:
        """
        :return: 1 if module not found
                 2 if circular import(or load)
                 3 if error while importing (or loading) a module
                 4 if handing error
        """

        from .avm import Interpreter, Frame

        p = self.__search_module(module_name)

        if p is None:
            return 1

        if p in self.__loading_paths:
            return 2

        if p in self.__loaded.keys():
            return self.__loaded[p]

        self.__loading_paths.append(p)
        remove_path = self.__loading_paths.remove
        
        cwd = getcwd()
        module_work_dir = os.path.dirname(p)

        chdir(module_work_dir)

        if self.__get_type(p) == 'py':
            remove_path(p)
            ns = self.__add_to_loaded(p, self.__load_py_namespace(p))
            chdir(cwd)
            return ns

        elif self.__get_type(p) == 'ail':
            ast = Parser(p).parse(Lex(p).lex())
            cobj = Compiler(filename=p).compile(ast).code_object

            frame = Frame(cobj, cobj.varnames, cobj.consts)
            frame.variable.update(BUILTINS)

            interpreter = MAIN_INTERPRETER_STATE.global_interpreter
            why = interpreter.exec_for_import(cobj, frame)

            v = frame.variable

            remove_path(p)
            chdir(cwd)

            if why == WHY_ERROR:
                return 3
            elif why == WHY_HANDLING_ERR:
                return 4

            return self.__add_to_loaded(p, v)

        remove_path(p)
        chdir(cwd)
        return 1


MAIN_LOADER = ModuleLoader(shared.GLOBAL_SHARED_DATA.find_path)
