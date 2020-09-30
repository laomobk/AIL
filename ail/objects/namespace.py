from .types import I_NAMESPACE_TYPE

from ..core.aobjects import (
    AILObject, AILObjectType, ObjectCreater, unpack_ailobj
)

from ..core.error import AILRuntimeError


def namespace_init(self: AILObject, namespace_name: str, getter, setter):
    self['__nsname__'] = namespace_name
    self['__nsgetter__'] = getter
    self['__nssetter__'] = setter


def namespace_setattr(self, name: str, value: AILObject) -> AILObject:
    try:
        return self['__nssetter__'](name, value)
    except TypeError as e:
        return AILRuntimeError('cannot set a field: %s' % str(e),
                               'BadNamespaceError')


def namespace_getattr(self, name: str) -> AILObject:
    try:
        return self['__nsgetter__'](name)
    except TypeError as e:
        return AILRuntimeError('cannot get a field: %s' % str(e),
                               'BadNamespaceError')


def namespace_str(self) -> str:
    return '<namespace %s>' % self['__nsname__']


def new_namespace(namespace_name: str, getter, setter) -> AILObject:
    return ObjectCreater.new_object(NAMESPACE_TYPE, namespace_name, getter, setter)


NAMESPACE_TYPE = AILObjectType('<namespace type>', I_NAMESPACE_TYPE,
                               __init__=namespace_init,
                               __setattr__=namespace_setattr,
                               __getattr__=namespace_getattr,
                               __str__=namespace_str,
                               __repr__=namespace_str,
                               )
