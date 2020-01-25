import aobjects as obj
from objects import wrapper
from objects import function
from objects import integer
from objects import string


def get_nezha_height():
    return 80  # cm


obj_w = obj.ObjectCreater.new_object(wrapper.WRAPPER_TYPE, 'Nezha')
obj_f = obj.ObjectCreater.new_object(function.PY_FUNCTION_TYPE, get_nezha_height)
obj_i = obj.ObjectCreater.new_object(integer.INTEGER_TYPE, 2)
obj_s = obj.ObjectCreater.new_object(string.STRING_TYPE, "Nezha")
obj_s2 = obj.ObjectCreater.new_object(string.STRING_TYPE, "Nezha")

print(obj_i['__eq__'](obj_i, obj_s))
