from .types import I_NAMESPACE_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater, unpack_ailobj,
    create_object,
)

from ..core.error import AILRuntimeError


def namespace_init(self: AILObject, 
                   ns_name: str, ns_dict: dict, ns_last: AILObject):
    self['__nsname__'] = ns_name
    self['__nsdict__'] = ns_dict
    self['__nslast__'] = ns_last


def namespace_setattr(self, name: str, value: AILObject) -> AILObject:
    self['__nsdict__'][name] = value


def namespace_getattr(self, name: str) -> AILObject:
    v = self['__nsdict__'].get(name)
    if v is None:
        last = self['__nslast__']
        if last is None:
            return AILRuntimeError(
                    'name \'%s\' is not defined' % name, 'NameError')
        return namespace_getattr(last, name)
    return v


def namespace_str(self) -> str:
    return '<namespace %s>' % self['__nsname__']


def new_namespace(ns_name: str, 
                  ns_dict: dict = None, 
                  ns_last: AILObject = None) -> AILObject:
    if default is None:
        default = dict()

    return create_object(
            NAMESPACE_TYPE, ns_name, ns_dict, ns_last)


NAMESPACE_TYPE = AILObjectType('<namespace type>', I_NAMESPACE_TYPE,
                               __init__=namespace_init,
                               __setattr__=namespace_setattr,
                               __getattr__=namespace_getattr,
                               __str__=namespace_str,
                               __repr__=namespace_str,
                               )
