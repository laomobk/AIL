import random
import time

from ail.core.aobjects import convert_to_ail_object, unpack_ailobj
from ail.core.error import AILRuntimeError

_IS_AIL_MODULE_ = True


def _random_random(seed=None):
    if seed is None:
        seed = time.time()

    seed = unpack_ailobj(seed)

    if type(seed) not in (int, float):
        return AILRuntimeError(
                'seed must be integer or float' 'TypeError')
    
    random.seed(seed)
    return random.random()


def _random_randint(a, b):
    a = unpack_ailobj(a)
    b = unpack_ailobj(b)

    if not isinstance(a, int) or not isinstance(b, int):
        return AILRuntimeError(
                'a, b must be an integer', 'TypeError')

    return random.randint(a, b)


_AIL_NAMESPACE_ = {
        'random': convert_to_ail_object(_random_random),
        'randint': convert_to_ail_object(_random_randint)
}

