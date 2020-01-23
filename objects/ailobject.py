# normal methods for ail object

def obj_str(aobj):
    oid = ido(aobj)
    hex_id = hex(oid)

    return '<%s object at %s>' % (aobj['__class__']['__name__'], hex_id)
