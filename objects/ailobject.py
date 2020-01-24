# normal methods for ail object


def obj_func_str(aobj):
    oid = id(aobj)
    hex_id = hex(oid)

    return '<AIL %s object at %s>' % (aobj['__class__'].name, hex_id)


def obj_func_init(aobj):
    '''
    :return : Do nothing...
    '''
    pass
