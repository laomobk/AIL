# Integer Pool

from objects import integer
import aobjects as obj

POOL_RANGE = (-5, 128)

class IntegerPool:
    def __init__(self):
        self.__pool = list()

    def __init_pool(self):
        mi, ma = POOL_RANGE

        for num in range(mi, ma):
            obj.ObjectCreater.new_object(integer.INTEGER_TYPE)