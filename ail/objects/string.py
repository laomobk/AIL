# String
from ..core import aobjects as obj
from ..core.aobjects import AILObject
from ..core.error import AILRuntimeError
from . import bool, integer, function
from . import types


_new_object = None
_compare_type = None
_convert_to_ail_object = None
_unpack_ailobj = None
_not_loaded = True


def _make_cache():
    global _not_loaded
    if _not_loaded:
        global _new_object
        global _compare_type
        global _convert_to_ail_object
        global _unpack_ailobj
        _new_object = obj.ObjectCreater.new_object
        _compare_type = obj.compare_type
        _convert_to_ail_object = obj.convert_to_ail_object
        _unpack_ailobj = obj.unpack_ailobj
        _not_loaded = False


def str_init(self, anystr: str):
    _make_cache()

    if type(anystr) == str:
        self['__value__'] = anystr
    elif type(anystr) == AILObject:
        if anystr['__class__'] == STRING_TYPE:
            self['__value__'] = anystr['__value__']
        else:
            pstr = self['__str__']()
            self['__value__'] = pstr

    else:
        self['__value__'] = str(anystr)

    self.set_hash_target(self['__value__'])


def str_add(self, ostr: AILObject) -> AILObject:
    _make_cache()

    if type(ostr) != AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')

    ss = self['__value__']
    os = ostr['__value__']

    rs = ss + str(os)

    return _new_object(STRING_TYPE, rs)


def str_muit(self, times: AILObject) -> AILObject:
    _make_cache()

    if type(times) != AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')

    if times['__class__'] != integer.INTEGER_TYPE:
        return AILRuntimeError('Not support \'*\' with type %s' % times['__class__'], 'TypeError')

    t = times['__value__']
    rs = self['__value__'] * t

    return _new_object(STRING_TYPE, rs)


def str_getitem(self, index: int):
    _make_cache()

    if isinstance(index, AILObject) and \
            index['__class__'] == integer.INTEGER_TYPE:
        i = index['__value__']

    elif isinstance(index, int):
        i = index

    else:
        return AILRuntimeError('array subscript index must be integer.',
                               'TypeError')

    l = self['__value__']

    if i >= len(l):
        return AILRuntimeError('index out of range (len %s, index %s)' %
                               (len(l), str(i)), 'IndexError')

    return _convert_to_ail_object(l[i])


def str_str(self):
    return '%s' % self['__value__']


def str_repr(self):
    return repr(self['__value__'])


def str_eq(self, ostr: AILObject) -> AILObject:
    _make_cache()

    if type(ostr) != AILObject:
        return AILRuntimeError('Cannot operate with Python object', 'TypeError')

    if ostr['__class__'] != STRING_TYPE:
        return AILRuntimeError('Not support \'==\' with type %s' % ostr['__class__'], 'TypeError')

    ss = self['__value__']
    os = ostr['__value__']

    if len(ss) != len(os):
        return _new_object(bool.BOOL_TYPE, 0)
    else:
        s = sum([a == b for a, b in zip(ss, os)])
        return _new_object(bool.BOOL_TYPE, s == len(os))


def str_len(self):
    return len(self['__value__'])


# methods of string


def str_join(self, array):
    _make_cache()

    array = _unpack_ailobj(array)

    if not isinstance(array, list):
        return AILRuntimeError('can only join an iterable', 'TypeError')

    if len(array) == 0:
        return ''

    val = self['__value__']
    result = ''

    for x in array[:-1]:
        result += str(x) + val

    result += str(array[-1])

    return result


def str_format(self, *items):
    _make_cache()

    items = tuple([_unpack_ailobj(o) for o in items])

    try:
        return self['__value__'] % items
    except TypeError as e:
        return AILRuntimeError(str(e), 'TypeError')


def str_encode(self, encoding='UTF-8'):
    encoding = obj.unpack_ailobj(encoding)
    if not isinstance(encoding, str):
        return AILRuntimeError(
            '\'encoding\' must be string', 'TypeError')

    val = self['__value__']  # type: str

    try:
        return val.encode(encoding)
    except UnicodeEncodeError as e:
        return AILRuntimeError(e.reason, 'UnicodeEncodeError')


str_is_digit = lambda self: str.isdigit(self['__value__'])
str_is_alpha = lambda self: str.isalpha(self['__value__'])
str_is_decimal = lambda self: str.isdecimal(self['__value__'])
str_is_numeric = lambda self: str.isnumeric(self['__value__'])
str_is_lower = lambda self: str.islower(self['__value__'])
str_is_upper = lambda self: str.isupper(self['__value__'])


STRING_METHODS = {
    'isAlpha': str_is_alpha,
    'isDecimal': str_is_decimal,
    'isDigit': str_is_digit,
    'isLower': str_is_lower,
    'isNumeric': str_is_numeric,
    'isUpper': str_is_upper,
    'join': str_join,
    'format': str_format,
    'encode': str_encode,
}


def convert_to_string(aobj) -> obj.AILObject:
    _make_cache()

    if isinstance(aobj, obj.AILObject):
        return aobj['__str__'](aobj)
    else:
        return _new_object(STRING_TYPE, str(aobj))


STRING_TYPE = obj.AILObjectType('<string type>', types.I_STR_TYPE,
                                STRING_METHODS,
                                __init__=str_init,
                                __add__=str_add,
                                # __muit__=str_muit,
                                __str__=str_str,
                                __repr__=str_repr,
                                __eq__=str_eq,
                                __getitem__=str_getitem,
                                __len__=str_len,
                                )
