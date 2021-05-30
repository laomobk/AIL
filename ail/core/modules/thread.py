from threading import Thread as _Thread, Lock


class Thread:
    def __new__(cls, target, args=None):
        if args is None:
            args = []
        return _Thread(target=target, args=args)


_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {
    'Thread': Thread,
    'Lock': Lock,
}
