from ail.core.aobjects import unpack_ailobj, convert_to_ail_object
from ail.core.error import AILRuntimeError


_IS_AIL_MODULE_ = True


def _escape(estr) -> str:
    s = unpack_ailobj(estr)

    if not isinstance(s, str):
        return AILRuntimeError('escape() needs a string.', 'TypeError')

    return eval('"""%s"""' % s)


_AIL_NAMESPACE_ = {
        'escape': convert_to_ail_object(_escape)
}
