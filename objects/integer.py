# Integer
from ..aobjects import AILObject, AILObjectType, compare_type, ObjectCreater
from ..error import AILRuntimeError

INTEGER_TYPE = AILObjectType('<AIL integer type>')


def int_add(self :AILObject, other :AILObject) -> AILObject:
    if not other['__value__']:   # do not have __value__ property
        return AILRuntimeError('Not support \'+\' with type %s' % str(other), 'TypeError')

    sv = self['__value__']