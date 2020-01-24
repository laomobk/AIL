# normal methods for ail object

def obj_func_str(aobj):
    oid = id(aobj)
    hex_id = hex(oid)

    return '<%s object at %s>' % (aobj['__class__']['__name__'], hex_id)


def obj_func_init(aobj):
    pass