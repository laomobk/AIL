from copy import copy
from inspect import isfunction, isbuiltin
from os import getcwd, chdir
from os.path import dirname
from types import MethodType
from typing import List

from . import exceptions as _exceptions
from . import shared as _shared

from ..core.aloader import MAIN_LOADER as _LOADER
from ..core.aobjects import AILObject, convert_to_ail_object
from ..core.error import AILRuntimeError as _RTError

from ..objects.null import _NULL_TYPE

_NONE = object()


def check_object(obj):
    if isinstance(obj, _RTError):
        raise _exceptions.AILRuntimeError('%s: %s' % (obj.err_type, obj.msg))
    return convert_object(obj)


def convert_to_ail_object_pyc(obj):
    if isinstance(obj, AILObjectWrapper):
        return getattr(obj, '_$ail_object')
    return convert_to_ail_object(obj)


def convert_object(obj):
    if isinstance(obj, AILObject):
        v = obj['__value__']
        if v is None and obj['__class__'] is _NULL_TYPE:
            return None
        elif type(v) in (int, str, float):
            return v
        elif type(v) is list:
            return [convert_object(o) for o in v]
        return AILObjectWrapper(obj)
    return obj


class AILModule:
    def __init__(self, name: str, path: str, globals: dict):
        setattr(self, '_$_module_globals', globals)
        setattr(self, '_$_name', name)
        setattr(self, '_$_path', path)

    def __getattr__(self, name: str):
        if name[:2] == '_$':
            return super().__getattribute__(name[2:])

        v = getattr(self, '_$_module_globals').get(name, _NONE)
        if v is _NONE:
            raise AttributeError('module \'%s\' has no attribute \'%s\'' %
                                 (getattr(self, '_$_name'), name))
        return v

    def __setattr__(self, name: str, value):
        if name[:2] == '_$':
            return super().__setattr__(name[2:], value)

        self._module_globals[name] = value

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
                ns = getattr(module_obj, '_$_module_globals', None)
                if not isinstance(module_obj, AILModule):
                    module_obj = None

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
            ns = _LOADER.get_py_namespace(path, False, True)
            if isinstance(ns, _RTError):
                raise ImportError(ns.msg)

            return {
                k: (convert_object(v) if isinstance(v, AILObject) else v)
                for k, v in
                ns.items()
            }

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


class AILObjectWrapper:
    def __init__(self, ail_object):
        setattr(self, '_$ail_object', ail_object)

    def __getattr__(self, name):
        if name[:2] == '_$':
            return super().__getattribute__(name[2:])
        elif name[:2] == name[-2:] == '__':
            return super().__getattribute__(name)

        o = getattr(self, '_$ail_object')
        v = o['__getattr__']

        if v is None:
            raise AttributeError(
                'object %s has no attribute \'%s\'' %
                (o['__class__'], name))

        return check_object(v(o, name))

    def __setattr__(self, name, value):
        if name[:2] == '_$':
            return super().__setattr__(name[2:], value)
        elif name[:2] == name[-2:] == '__':
            return super().__setattr__(name, value)

        o = getattr(self, '_$ail_object')
        v = o['__setattr__']

        if v is None:
            raise AttributeError(
                'cannot set attribute to \'%s\'' % o['__class__'])

        return check_object(v(o, name, convert_to_ail_object(value)))

    def __str__(self):
        o = getattr(self, '_$ail_object')
        v = o['__str__']

        if v is None:
            return '<AILObject Wrapper at %s>' % (hex(id(self)))

        return check_object(v(o))

    def __repr__(self):
        o = getattr(self, '_$ail_object')
        v = o['__repr__']

        if v is None:
            return '<AILObject Wrapper at %s>' % (hex(id(self)))

        return check_object(v(o))

    def __call__(self, *args):
        o = getattr(self, '_$ail_object')
        v = o['__pyfunction__']

        if v is None:
            raise AttributeError(
                '\'%s\' object is not callable' % o['__class__'])

        args = [convert_to_ail_object_pyc(o) for o in args]

        if o['__this__'] is not None:
            return check_object(v(o, *args))
        return check_object(v(*args))


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
