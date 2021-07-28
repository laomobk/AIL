
_IS_AIL_MODULE_ = True


def _escape(estr) -> str:
    return eval('"""%s"""' % estr)


_AIL_NAMESPACE_ = {
        'escape': _escape
}
