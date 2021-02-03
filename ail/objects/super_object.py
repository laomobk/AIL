
from ..core.aobjects import convert_to_ail_object
from ..core.error import AILRuntimeError


def super_init(self, instance, bases, _class):
    self['__this_class__'] = _class
    self['__instance__'] = instance
    self['__base__'] = bases
    self['__base_order__'] = _calculate_base_order(bases)


def _calculate_base_order(bases):
    return []


def _find_class_from_order(self, name):
    order = self['__base_order__']
    assert isinstance(order, dict)
    
    for base in order:
        b_dict = base['__dict__']
        assert isinstance(b_dict, dict)

        val = b_dict.get(name)
        if val is not None:
            return base

    return None


def super_getattr(self, name):
    cls = _find_class_from_order(self, name)
    
    if cls is not None:
        return cls['__dict__'][name]

    return AILRuntimeError('super: cannot find attribute from super class')


def super_setattr(self, name, value):
    cls = _find_class_from_order(self, name)

    if cls is not None:
        cls['__dict__'][name] = convert_to_ail_object(value)


def super_str(self):
    cls = self['__this_class__']
    return '<super of %s>' % str(cls)

