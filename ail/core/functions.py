
from copy import copy
from os.path import split
from inspect import isfunction, isbuiltin
from typing import List, Dict, Union

from .objects import AILImporter as _AILImporter, AILStruct as _AILStruct, Namespace

_IMPORTER = _AILImporter()


def raise_exception(err_obj):
    raise err_obj


def convert_to_namespace(namespace_func):
    func_locals = namespace_func()
    return Namespace(namespace_func.__name__, func_locals)


_eval_cache = None


def ail_eval(source: str, globals=None, locals=None):
    global _eval_cache
    if _eval_cache is None:
        from ..core.pyexec import ail_eval as _eval_cache
    return _eval_cache(source, globals=globals, locals=locals)


def ail_using(ns_obj: 'Namespace', namespace: dict):
    namespace.update(ns_obj.__dict__)


def ail_match(target, patterns: list, only_constant: bool) -> bool:
    if only_constant:
        return target in patterns

    for pattern in patterns:
        if hasattr(pattern, '__match__'):
            if pattern.__match__(target):
                return True
        else:
            return target == pattern

    return False


def ail_input(prompt: str, value_count: int):
    m = input(prompt)
    if value_count == 1:
        return m
    if value_count == 0:
        return None

    vals = m.split(maxsplit=value_count)
    if len(vals) < value_count:
        raise ValueError('no enough value to split')

    return vals


def _get_module_name(full_name: str):
    if '/' not in full_name:
        return full_name
    return split(full_name)[-1]


def ail_import(
        mode: int, name: str, namespace: dict, 
        alias: str=None, members: List[str] = []):
    """
    :param mode: 0 -> load | 1 -> import
    """
    if alias is None:
        alias = name

    if namespace is None:
        namespace = {}
    
    _IMPORTER.import_module(mode, name, namespace, alias, members)
    
    module_name = _get_module_name(name)
    if mode == 1:
        return namespace.values() if members else namespace[module_name]
    return None


def bind_function(name: str, struct: _AILStruct):
    def outer_wrapper(func):
        if not isinstance(struct, _AILStruct) or (
                struct.__ail_as_instance__ or struct.__ail_as_object__):
            raise TypeError('function must bind on a struct')
        elif not (isfunction(func) or isbuiltin(func)):
            raise TypeError('only function can be bound')
        struct.__bound_functions__[name] = func
        return func
    return outer_wrapper


def contains(o, iterable):
    return o in iterable


def make_struct(name: str, members: List[str], protected: List[str]) -> _AILStruct:
    if not isinstance(name, str):
        raise TypeError('struct name must be string')
    if not isinstance(members, list) or not isinstance(protected, list):
        raise TypeError('struct members or protecteds must be list')
    return _AILStruct(name, members, protected)


def new_struct_object(struct: _AILStruct, attrs: Union[Dict, List] = None):
    if not isinstance(struct, _AILStruct):
        raise TypeError('new() requires a struct')

    obj = copy(struct)
    obj.__ail_dict__ = dict()
    obj.__ail_as_object__ = True

    members_len = len(obj.__ail_members__)

    if isinstance(attrs, dict):
        items = attrs.items()
        try:
            obj.__ail_as_instance__ = True
            for k, v in items:
                setattr(obj, k, v)
        finally:
            obj.__ail_as_instance__ = False
    elif isinstance(attrs, list):
        if len(attrs) != members_len:
            raise ValueError('struct \'%s\' initializing needs %s value(s)' % 
                             (obj.__ail_struct_name__, members_len))
        try:
            obj.__ail_as_instance__ = True
            for k, v in zip(obj.__ail_members__, attrs):
                setattr(obj, k, v)
        finally:
            obj.__ail_as_instance__ = False

    instance = copy(obj)
    instance.__ail_as_instance__ = True

    for name, func in struct.__bound_functions__.items():
        v = struct.__ail_check_bound__(instance, func, True)
        setattr(instance, name, v)

    return obj


def func_fnum(x):
    return x

