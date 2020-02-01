import aobjects as obj
from objects import types

def null_str(self):
    return 'null'


_NULL_TYPE = obj.AILObjectType('<null type>', types.I_NULL_TYPE, 
                                __str__=null_str)

null = obj.ObjectCreater.new_object(_NULL_TYPE)
