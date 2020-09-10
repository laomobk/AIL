from core.agc import GC
from core import aobjects as obj
import sys

def test():
    o1 = obj.ObjectCreater.new_object(obj.AILObjectType('NOTYPE'))
    o2 = obj.ObjectCreater.new_object(obj.AILObjectType('NOTYPE'))

    o2['a'] = o1
    o1['b'] = o2

    gc = GC()

    print(gc.register_object(o1))
    print(gc.register_object(o2))

    print('o1 ref =', o1.reference)
    print('o2 ref =', o2.reference)

    gc.set_output_stream(sys.stdout)

    gc._free(o1)
    gc._free(o2)
    print('free o1, o2')

    print('o1 ref =', o1.reference)
    print('o2 ref =', o2.reference)

    gc.gc()