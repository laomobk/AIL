from ail.core.version import (AIL_VERSION, AIL_VERSION_STATE,
                              AIL_SUB_VERSION, AIL_MAIN_VERSION)
from ail.core.aobjects import convert_to_ail_object, unpack_ailobj
from ail.objects.class_object import (
    new_class, new_object, 
    object_getattr_with_default, object_setattr
)


def _class_version___str__(self):
    main_v = object_getattr_with_default(self, '_main_version')
    sub_v = object_getattr_with_default(self, '_sub_version')
    v_state = object_getattr_with_default(self, '_version_state')
    return '%s.%s %s' % (
                         main_v,
                         '.'.join([str(x) for x in unpack_ailobj(sub_v)]),
                         v_state)


def _class_version___repr__(self):
    main_v = object_getattr_with_default(self, '_main_version')
    sub_v = object_getattr_with_default(self, '_sub_version')
    v_state = object_getattr_with_default(self, '_version_state')

    return 'AILVersion(%s, %s, %s)' % (repr(main_v), 
                                       repr(sub_v), 
                                       repr(v_state))


def _class_version___init__(self, main_v, sub_v, v_state):
    object_setattr(self, '_main_version', main_v)
    object_setattr(self, '_sub_version', sub_v)
    object_setattr(self, '_version_state', v_state)


_CLASS_VERSION = new_class(
    '_AILVersion', [],
    {
        '__init__': convert_to_ail_object(_class_version___init__),
        '__str__': convert_to_ail_object(_class_version___str__),
        '__repr__': convert_to_ail_object(_class_version___repr__),
    }
)


def _version_new_version():
    return new_object(
                      _CLASS_VERSION, 
                      convert_to_ail_object(AIL_MAIN_VERSION),
                      convert_to_ail_object(AIL_SUB_VERSION),
                      convert_to_ail_object(AIL_VERSION_STATE),)


_IS_AIL_MODULE_ = True

_AIL_NAMESPACE_ = {
    'AIL_MAIN_VERSION': AIL_MAIN_VERSION,
    'AIL_SUB_VERSION': AIL_SUB_VERSION,
    'AIL_VERSION': AIL_VERSION,
    'AIL_VERSION_STATE': AIL_VERSION_STATE,
    'versionInfo': _version_new_version(),
}

