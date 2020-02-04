# module loader

import os.path
from alex import Lex
from aparser import Parser
from acompiler import Compiler
import error

import aobjects as objs

import debugger

_ALLOW_FILE_TYPE = ('ail', 'py')

LOAD_MODULE_PATH = ('.', 'lib/')


'''
如果你想要创建一个 AIL 的 Python 模块
请务必在模块中定义一个 '_AIL_NAMESPACE_' 字典
AIL 会加载这个字典，作为 namespace 导入到 AIL 主名称空间中
'''


class ModuleLoader:
    def __init__(self, paths :list):
        self.__load_path = paths
        self.__loaded = {}

    def __search_module(self, name :str) -> str:
        '''
        :return: module path if found else None
        '''
        maybe_file = ['%s.%s' % (name, x) for x in _ALLOW_FILE_TYPE]

        for p in self.__load_path:
            for f in os.listdir(p):
                fp = os.path.join(p, f)
                if os.path.exists(fp) and os.path.isfile(fp):
                    if os.path.split(fp)[-1] in maybe_file:
                        return fp
        return None

    def __load_py_namespace(self, pypath):
        v = {}

        try:
            cobj = compile(open(pypath).read(), pypath, 'exec')
            exec(cobj, v)
        except Exception as e:
            return error.AILRuntimeError(
                '%s : %s' % (type(e).__name__, str(e)), 'ErrorWhileLoading')

        if '_AIL_NAMESPACE_' in v:
            nsp = v['_AIL_NAMESPACE_']

            # convert all objects to AILObject
            for k, v in nsp.items():
                nsp[k] = objs.convert_to_ail_object(v)

            return nsp

        return {}

    def __get_type(self, fp :str):
        fn = os.path.split(fp)[-1]
        fns = fn.split('.')

        if len(fns) > 1 and fns[-1] in _ALLOW_FILE_TYPE:
            return fns[-1]

    def __add_to_loaded(self, name :str, namespace :dict):
        if namespace is not None:
            self.__loaded[name] = namespace
        return namespace

    def load_namespace(self, module_name :str) -> dict:
        from avm import Interpreter, Frame

        if module_name in self.__loaded.keys():
            return self.__loaded[module_name]

        p = self.__search_module(module_name)

        if p is None:
            return None

        if self.__get_type(p) == 'py':
            return self.__add_to_loaded(module_name, self.__load_py_namespace(p))

        elif self.__get_type(p) == 'ail':
            ast = Parser(Lex(p).lex(), p).parse()
            cobj = Compiler(ast, filename=p).compile(ast).code_object

            frame = Frame(cobj, cobj.varnames, cobj.consts)

            Interpreter().exec(cobj, frame)

            v = frame.variable

            return self.__add_to_loaded(module_name, v)

        return None


MAIN_LOADER = ModuleLoader(LOAD_MODULE_PATH)

