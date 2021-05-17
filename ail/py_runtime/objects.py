
from typing import List

from . import exceptions as _exceptions

from ..core.aloader import MAIN_LOADER as _LOADER

_NONE = object()


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


class AILImporter:
    def __init__(self):
        pass

    def import_module(self,
            mode: int, name: str, namespace: dict, 
            alias: str, members: List[str]):

        path = _LOADER.search_module(name)
        if path is None:
            raise _exceptions.AILModuleNotFoundError(
                    'cannot find module \'%s\'' % name)

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

    def get_namespace(self, path: str) -> dict:
        if _LOADER.get_type(path) in ('py', 'ailp'):
            return _LOADER.get_py_namespace(path, False)

        # exec and get namespace
        from ..core.pyexec import exec_as_python as _exec

        try:
            module_globals = dict()
            source = open(path, encoding='UTF-8').read()

            _exec(source, path, module_globals)

            return module_globals
        except FileNotFoundError as e:
            raise _exceptions.AILModuleNotFoundError(
                    'cannot find module from given path: \'%s\': %s' % 
                    (path, str(e)))
        except UnicodeDecodeError as e:
            raise _exceptions.AILImportError('cannot decode module with UTF-8')

