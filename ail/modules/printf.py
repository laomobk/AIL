from ail.core.aobjects import unpack_ailobj, convert_to_ail_object
from ail.core.error import AILRuntimeError


_IS_AIL_MODULE_ = True


def _printf(x, *format):
    xs = unpack_ailobj(x)

    fs = tuple([unpack_ailobj(x) for x in format])

    print(xs % fs, end='')


_AIL_NAMESPACE_ = {
        'printf': convert_to_ail_object(_printf)
}
