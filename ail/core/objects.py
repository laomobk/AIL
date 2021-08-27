from inspect import isfunction, isbuiltin
from os import getcwd, chdir
from os.path import dirname
from types import MethodType
from typing import List

from ail.core import exceptions as _exceptions
from . import shared as _shared

from ail.core.aloader import MAIN_LOADER as _LOADER

_NONE = object()


class AILModule:
    def __init__(self, name: str, path: str, globals: dict):
        self.__dict__ = globals

        setattr(self, '_$_name', name)
        setattr(self, '_$_path', path)

    def __str__(self):
        return '<AILModule \'%s\' from \'%s\'>' % (
            getattr(self, '_$_name'), getattr(self, '_$_path')
        )

    __repr__ = __str__


class AILImporter:
    def __init__(self):
        self.__loading_modules = []

    @staticmethod
    def get_export(namespace: dict, exports: dict) -> dict:
        if exports is None:
            return namespace

        if isinstance(exports, dict):
            return exports
        else:
            try:
                ns = dict()
                for k in exports:
                    if k not in namespace:
                        raise ImportError('Cannot export name %s in module' % k)
                    ns[k] = namespace[k]
                return ns
            except TypeError:
                raise ImportError('__export__ must be a dict or a iterable object')

    def import_module(self,
                      mode: int, name: str, namespace: dict,
                      alias: str, members: List[str]):

        path = self.get_path(name)

        if path in self.__loading_modules:
            raise ImportError('Cannot import module \'%s\' ' % name +
                              '(may caused circular import)')

        self.__loading_modules.append(path)

        try:
            from ..core.pyexec import StopExec

            module_obj = None

            ns = dict()

            if path in _shared.loaded_modules:
                module_obj = _shared.loaded_modules[path]
                if not isinstance(module_obj, AILModule):
                    module_obj = None
                else:
                    ns = module_obj.__dict__

            if module_obj is None:
                ns = self.get_namespace(path, self.get_source(path))
                ns = self.get_export(ns, ns.get('__export__', None))
                module_obj = AILModule(name, path, ns)

                _shared.loaded_modules[path] = module_obj

            if mode == 0:  # load
                namespace.update(ns)
            elif mode == 1:
                if len(members) > 0:
                    for member in members:
                        v = ns.get(member, _NONE)
                        if v is _NONE:
                            raise ImportError(
                                'cannot import member \'%s\' from \'%s\'' %
                                (member, name))
                        namespace[member] = v
                    return

                namespace[alias] = module_obj
        finally:
            self.__loading_modules.remove(path)

    @staticmethod
    def get_path(name: str, default=_NONE) -> str:
        path = _LOADER.search_module(name)
        if path is None and default is _NONE:
            raise ModuleNotFoundError(
                'cannot find module \'%s\'' % name)
        return path

    @staticmethod
    def get_source(path: str) -> str:
        return open(path, encoding='UTF-8').read()

    @staticmethod
    def get_namespace(path: str, source: str) -> dict:
        if _LOADER.get_type(path) in ('py', 'ailp'):
            ns = _LOADER.get_py_namespace(path)

            return ns

        # exec and get namespace
        from ..core.pyexec import exec_as_python as _exec

        cwd = getcwd()

        try:
            from . import AIL_PY_GLOBAL
            module_globals = AIL_PY_GLOBAL.copy()

            module_work_dir = dirname(path)

            chdir(module_work_dir)

            status = _exec(source, path, module_globals, False)

            return module_globals
        except FileNotFoundError as e:
            raise _exceptions.AILModuleNotFoundError(
                'cannot find module from given path: \'%s\': %s' %
                (path, str(e)))
        except UnicodeDecodeError as e:
            raise _exceptions.AILImportError('cannot decode module with UTF-8')
        finally:
            chdir(cwd)


class AILStruct:
    def __init__(self, name: str, members: List[str], protected: List[str]):
        self.__ail_protected__ = tuple(protected)
        self.__ail_members__ = tuple(members)
        self.__ail_as_instance__ = False
        self.__ail_struct_name__ = name
        self.__ail_as_object__ = False
        self.__bound_functions__ = {}

        self.__ail_dict__ = dict()

        self.__init_members__()

    def __ail_check_bound__(self, instance, target, try_bound: bool = False):
        is_func = isfunction(target) or isbuiltin(target)
        if not is_func:
            if try_bound:
                return target
            raise TypeError('bound target must be a function')
        method = MethodType(target, instance)
        return method

    def __set_bound_function__(self, name: str, func):
        self.__bound_functions__[name] = func

    def __init_members__(self):
        try:
            self.__ail_as_instance__ = True
            for m in self.__ail_members__:
                setattr(self, m, None)
        finally:
            self.__ail_as_instance__ = False

    def __getattr__(self, name: str):
        if name[:2] == name[-2:] == '__':
            return super().__getattribute__(name)
        elif name[:2] == '__':
            if not self.__ail_as_instance__:
                raise AttributeError('struct \'%s\' has no attribute \'%s\'' %
                                     (self.__ail_struct_name__, name))
        if name in self.__ail_dict__:
            return self.__ail_dict__[name]
        else:
            raise AttributeError('struct \'%s\' has no attribute \'%s\'' %
                                 (self.__ail_struct_name__, name))

    def __setattr__(self, name: str, value):
        if name[:2] == name[-2:] == '__':
            return super().__setattr__(name, value)

        elif name[:2] == '__':
            if not self.__ail_as_instance__:
                raise AttributeError('struct \'%s\' has no attribute \'%s\'' %
                                     (self.__ail_struct_name__, name))

        elif name in self.__ail_protected__ and not self.__ail_as_instance__:
            raise AttributeError('readonly attribute')

        elif self.__ail_as_instance__:
            v = self.__ail_check_bound__(self, value, True)
            self.__ail_dict__[name] = v

        elif self.__ail_as_object__:
            if name in self.__ail_protected__:
                raise AttributeError('cannot set a protected attribute \'%s\'' % name)
            self.__ail_dict__[name] = value

        elif name not in self.__ail_members__:
            raise AttributeError('struct \'%s\' has no attribute \'%s\'' %
                                 (self.__ail_struct_name__, name))
        else:
            raise AttributeError('cannot set attribute to struct')
        # super().__setattr__(name, value)

    def __str__(self) -> str:
        if self.__ail_as_object__:
            return '<struct \'%s\' object at %s>' % \
                   (self.__ail_struct_name__, hex(id(self)))
        return '<struct \'%s\'>' % self.__ail_struct_name__

    __repr__ = __str__


class ObjectPattern:
    def __init__(self, type_: type, kv_dict: dict):
        self.__type = type_
        self.__kv_dict = kv_dict

    def __match__(self, target) -> bool:
        if not isinstance(target, self.__type):
            return False

        for k, v in self.__kv_dict.items():
            if not hasattr(target, k) or getattr(target, k) != v:
                return False

        return True


class Namespace:
    def __init__(self, name, namespace_locals):
        self.__dict__ = namespace_locals
        self.__name__ = name

    def __str__(self) -> str:
        return '<namespace \'%s\' at %s>' % (self.__name__, hex(id(self)))

    __repr__ = __str__
