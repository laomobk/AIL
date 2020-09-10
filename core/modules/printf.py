from core.aobjects import unpack_ailobj, convert_to_ail_object
from core.error import AILRuntimeError


_IS_AIL_MODULE_ = True


def _printf(x, format):
    xs = unpack_ailobj(x)
    fs = unpack_ailobj(format)

    if not isinstance(fs, list):
        return AILRuntimeError('printf() needs a list as \'format\'', 'TypeError')

    fs = tuple([str(unpack_ailobj(x)) for x in fs])

    print(xs % fs, end='')


_AIL_NAMESPACE_ = {
        'printf': convert_to_ail_object(_printf)
}
