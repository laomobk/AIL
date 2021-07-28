
_IS_AIL_MODULE_ = True


def _printf(x, *format):
    print(x % format, end='')


_AIL_NAMESPACE_ = {
        'printf': _printf
}
