
from typing import List

from . import exceptions as _exceptions

from ..core.aloader import MAIN_LOADER as _LOADER
from ..core.aobjects import AILObject, convert_to_ail_object
from ..core.error import AILRuntimeError as _RTError

from ..objects.null import _NULL_TYPE


_NONE = object()


def check_object(obj):
    if isinstance(obj, _RTError):
        raise _exceptions.AILRuntimeError('%s: %s' % (obj.err_type, obj.msg))
    return convert_object(obj)


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

    def import_module(self,
            mode: int, name: str, namespace: dict, 
            alias: str, members: List[str]):

        path = _LOADER.search_module(name)
        if path is None:
            raise _exceptions.AILModuleNotFoundError(
                    'cannot find module \'%s\'' % name)

        if path in self.__loading_modules:
            raise ImportError('Cannot import module \'%s\' ' % name +
                    '(may caused circular import)')

        self.__loading_modules.append(path)

        try:
            ns = self.get_namespace(path)

            if mode == 0:  # load
                namespace.update(ns)
            elif mode == 1:
                if len(members) > 0:
                    for member in members:
                        v = ns.get(member, None)
                        if v is None:
                            raise _exceptions.AILImportError(
                                'cannot import member \'%s\' from \'%s\'' % 
                                (member, name))
                        namespace[member] = v
                        return

                module_obj = AILModule(name, path, ns)
                namespace[alias] = module_obj
        finally:
            self.__loading_modules.remove(path)

    def get_namespace(self, path: str) -> dict:
        if _LOADER.get_type(path) in ('py', 'ailp'):
            ns = _LOADER.get_py_namespace(path, False)
            if isinstance(ns, _RTError):
                raise ImportError(ns.msg)

            return {
                k: (convert_object(v) if isinstance(v, AILObject) else v)
                for k, v in 
                ns.items()
            }

        # exec and get namespace
        from ..core.pyexec import exec_as_python as _exec

        try:
            from . import AIL_PY_GLOBAL
            module_globals = AIL_PY_GLOBAL
            source = open(path, encoding='UTF-8').read()

            _exec(source, path, module_globals)

            return module_globals
        except FileNotFoundError as e:
            raise _exceptions.AILModuleNotFoundError(
                    'cannot find module from given path: \'%s\': %s' % 
                    (path, str(e)))
        except UnicodeDecodeError as e:
            raise _exceptions.AILImportError('cannot decode module with UTF-8')


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

        args = [convert_to_ail_object(o) for o in args]

        if o['__this__'] is not None:
            return check_object(v(o, *args))
        return check_object(v(*args))

