
from builtins import next as _next


class IterationState:
    def __init__(self, state: str):
        self.state = state

    def __str__(self):
        return '<IterationState: %s>' % self.state

    __repr__ = __str__


STOP = IterationState('Stop')


def next(iterator):
    try:
        return _next(iterator)
    except StopIteration:
        return STOP


_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {
    'next': next,
    'STOP': STOP,
    'IterationState': IterationState,
}

