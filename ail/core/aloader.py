# module loader

import os.path

from traceback import format_exc

from .alex import Lex
from .aparser import Parser
from .acompiler import Compiler

from . import aobjects as objs, error
from . import shared

_ALLOW_FILE_TYPE = ('ail', 'py')


'''
如果你想要创建一个 AIL 的 Python 模块
请务必在模块中定义一个 '_AIL_NAMESPACE_' 字典
且要在该Python模块中设置 _IS_AIL_MODULE_ = True 字段！
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

        for mfp in maybe_file:
            for sp in self.__load_path:
                absfp = os.path.abspath(sp)
                jfp = os.path.join(absfp, mfp)

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
                '%s' % excs, 'ErrorWhileLoading')

        is_mod = v.get('_IS_AIL_MODULE_', None)

        if is_mod is not True:
            return error.AILRuntimeError(
                '%s is not an AIL MODULE!' % pypath, 'ErrorWhileLoading')

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
        '''return -1 if module not found'''
        from .avm import Interpreter, Frame

        module_name = module_name.replace('.', '/')

        if module_name in self.__loaded.keys():
            return self.__loaded[module_name]

        p = self.__search_module(module_name)

        if p is None:
            return -1

        if self.__get_type(p) == 'py':
            return self.__add_to_loaded(module_name, self.__load_py_namespace(p))

        elif self.__get_type(p) == 'ail':
            ast = Parser(p).parse(Lex(p).lex())
            cobj = Compiler(filename=p).compile(ast).code_object

            frame = Frame(cobj, cobj.varnames, cobj.consts)

            Interpreter().exec(cobj, frame)

            v = frame.variable

            return self.__add_to_loaded(module_name, v)

        return -1


MAIN_LOADER = ModuleLoader(shared.GLOBAL_SHARED_DATA.find_path)

