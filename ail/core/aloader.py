# module loader

import os.path

from . import error
from . import shared

_ALLOW_FILE_TYPE = ('ail', 'py', 'ailp')

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

    def __load_py_namespace(self, pypath):
        v = {}

        cobj = compile(
                    open(pypath, encoding='UTF-8').read(), pypath, 'exec')
        exec(cobj, v)

        is_mod = v.get('_IS_AIL_MODULE_', False)
        is_mod = v.get('_AIL_MODULE_', False) if not is_mod else True
        is_pyc_module = v.get('_AIL_PYC_MODULE_', False)
        has_namespace = '_AIL_NAMESPACE_' in v

        if not (is_mod or is_pyc_module) or not has_namespace:
            raise ModuleNotFoundError(
                '%s is not an AIL MODULE!' % pypath, 'LoadError')

        return v.get('_AIL_NAMESPACE_', {})

    get_py_namespace = __load_py_namespace

    def __get_type(self, fp: str):
        fn = os.path.split(fp)[-1]
        fns = fn.split('.')

        if len(fns) > 1 and fns[-1] in _ALLOW_FILE_TYPE:
            return fns[-1]

    get_type = __get_type


MAIN_LOADER = ModuleLoader()
