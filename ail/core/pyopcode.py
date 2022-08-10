

OPMAP = {}
OPCODE_TO_NAME_MAP = {}
OPCODE_STACK_EFFECT = {}

EFCT_UNCERTAIN_EFFECT = object()
EFCT_DYNAMIC_EFFECT = object()


def _register_opcode(code, name) -> int:
    OPMAP[name] = code
    OPCODE_TO_NAME_MAP[code] = name
    return code


def _stack_effect(code, effect) -> int:
    OPCODE_STACK_EFFECT[code] = effect
    return code


POP_TOP = _stack_effect(_register_opcode(1, 'POP_TOP'), -1)
ROT_TWO = _register_opcode(2, 'ROT_TWO')
ROT_THREE = _register_opcode(3, 'ROT_THREE')
DUP_TOP = _stack_effect(_register_opcode(4, 'DUP_TOP'), 1)
DUP_TOP_TWO = _stack_effect(_register_opcode(5, 'DUP_TOP_TWO'), 2)
ROT_FOUR = _register_opcode(6, 'ROT_FOUR')
NOP = _register_opcode(9, 'NOP')
UNARY_POSITIVE = _register_opcode(10, 'UNARY_POSITIVE')
UNARY_NEGATIVE = _register_opcode(11, 'UNARY_NEGATIVE')
UNARY_NOT = _register_opcode(12, 'UNARY_NOT')
UNARY_INVERT = _register_opcode(15, 'UNARY_INVERT')
BINARY_MATRIX_MULTIPLY = _stack_effect(_register_opcode(16, 'BINARY_MATRIX_MULTIPLY'), -1)
INPLACE_MATRIX_MULTIPLY = _stack_effect(_register_opcode(17, 'INPLACE_MATRIX_MULTIPLY'), -1)
BINARY_POWER = _stack_effect(_register_opcode(19, 'BINARY_POWER'), -1)
BINARY_MULTIPLY = _stack_effect(_register_opcode(20, 'BINARY_MULTIPLY'), -1)
BINARY_MODULO = _stack_effect(_register_opcode(22, 'BINARY_MODULO'), -1)
BINARY_ADD = _stack_effect(_register_opcode(23, 'BINARY_ADD'), -1)
BINARY_SUBTRACT = _stack_effect(_register_opcode(24, 'BINARY_SUBTRACT'), -1)
BINARY_SUBSCR = _stack_effect(_register_opcode(25, 'BINARY_SUBSCR'), -1)
BINARY_FLOOR_DIVIDE = _stack_effect(_register_opcode(26, 'BINARY_FLOOR_DIVIDE'), -1)
BINARY_TRUE_DIVIDE = _stack_effect(_register_opcode(27, 'BINARY_TRUE_DIVIDE'), -1)
INPLACE_FLOOR_DIVIDE = _stack_effect(_register_opcode(28, 'INPLACE_FLOOR_DIVIDE'), -1)
INPLACE_TRUE_DIVIDE = _stack_effect(_register_opcode(29, 'INPLACE_TRUE_DIVIDE'), -1)
GET_AITER = _stack_effect(_register_opcode(50, 'GET_AITER'), 1)
GET_ANEXT = _stack_effect(_register_opcode(51, 'GET_ANEXT'), 1)
BEFORE_ASYNC_WITH = _register_opcode(52, 'BEFORE_ASYNC_WITH')
BEGIN_FINALLY = _register_opcode(53, 'BEGIN_FINALLY')
END_ASYNC_FOR = _register_opcode(54, 'END_ASYNC_FOR')
INPLACE_ADD = _stack_effect(_register_opcode(55, 'INPLACE_ADD'), -1)
INPLACE_SUBTRACT = _stack_effect(_register_opcode(56, 'INPLACE_SUBTRACT'), -1)
INPLACE_MULTIPLY = _stack_effect(_register_opcode(57, 'INPLACE_MULTIPLY'), -1)
INPLACE_MODULO = _stack_effect(_register_opcode(59, 'INPLACE_MODULO'), -1)
STORE_SUBSCR = _stack_effect(_register_opcode(60, 'STORE_SUBSCR'), -3)
DELETE_SUBSCR = _stack_effect(_register_opcode(61, 'DELETE_SUBSCR'), -2)
BINARY_LSHIFT = _stack_effect(_register_opcode(62, 'BINARY_LSHIFT'), -1)
BINARY_RSHIFT = _stack_effect(_register_opcode(63, 'BINARY_RSHIFT'), -1)
BINARY_AND = _stack_effect(_register_opcode(64, 'BINARY_AND'), -1)
BINARY_XOR = _stack_effect(_register_opcode(65, 'BINARY_XOR'), -1)
BINARY_OR = _stack_effect(_register_opcode(66, 'BINARY_OR'), -1)
INPLACE_POWER = _stack_effect(_register_opcode(67, 'INPLACE_POWER'), -1)
GET_ITER = _stack_effect(_register_opcode(68, 'GET_ITER'), 1)
GET_YIELD_FROM_ITER = _stack_effect(_register_opcode(69, 'GET_YIELD_FROM_ITER'), 1)
PRINT_EXPR = _stack_effect(_register_opcode(70, 'PRINT_EXPR'), -1)
LOAD_BUILD_CLASS = _stack_effect(_register_opcode(71, 'LOAD_BUILD_CLASS'), 1)
YIELD_FROM = _stack_effect(_register_opcode(72, 'YIELD_FROM'), -1)
GET_AWAITABLE = _stack_effect(_register_opcode(73, 'GET_AWAITABLE'), 1)
INPLACE_LSHIFT = _stack_effect(_register_opcode(75, 'INPLACE_LSHIFT'), -1)
INPLACE_RSHIFT = _stack_effect(_register_opcode(76, 'INPLACE_RSHIFT'), -1)
INPLACE_AND = _stack_effect(_register_opcode(77, 'INPLACE_AND'), -1)
INPLACE_XOR = _stack_effect(_register_opcode(78, 'INPLACE_XOR'), -1)
INPLACE_OR = _stack_effect(_register_opcode(79, 'INPLACE_OR'), -1)
WITH_CLEANUP_START = _register_opcode(81, 'WITH_CLEANUP_START')
WITH_CLEANUP_FINISH = _register_opcode(82, 'WITH_CLEANUP_FINISH')
RETURN_VALUE = _stack_effect(_register_opcode(83, 'RETURN_VALUE'), -1)
IMPORT_STAR = _stack_effect(_register_opcode(84, 'IMPORT_STAR'), -1)
SETUP_ANNOTATIONS = _register_opcode(85, 'SETUP_ANNOTATIONS')
YIELD_VALUE = _stack_effect(_register_opcode(86, 'YIELD_VALUE'), -1)
POP_BLOCK = _register_opcode(87, 'POP_BLOCK')
END_FINALLY = _register_opcode(88, 'END_FINALLY')
POP_EXCEPT = _register_opcode(89, 'POP_EXCEPT')
STORE_NAME = _stack_effect(_register_opcode(90, 'STORE_NAME'), -1)
DELETE_NAME = _register_opcode(91, 'DELETE_NAME')
UNPACK_SEQUENCE = _stack_effect(_register_opcode(92, 'UNPACK_SEQUENCE'), EFCT_DYNAMIC_EFFECT)
FOR_ITER = _stack_effect(_register_opcode(93, 'FOR_ITER'), 1)
UNPACK_EX = _stack_effect(_register_opcode(94, 'UNPACK_EX'), EFCT_DYNAMIC_EFFECT)
STORE_ATTR = _stack_effect(_register_opcode(95, 'STORE_ATTR'), -2)
DELETE_ATTR = _stack_effect(_register_opcode(96, 'DELETE_ATTR'), -1)
STORE_GLOBAL = _stack_effect(_register_opcode(97, 'STORE_GLOBAL'), -1)
DELETE_GLOBAL = _register_opcode(98, 'DELETE_GLOBAL')
LOAD_CONST = _stack_effect(_register_opcode(100, 'LOAD_CONST'), 1)
LOAD_NAME = _stack_effect(_register_opcode(101, 'LOAD_NAME'), 1)
BUILD_TUPLE = _stack_effect(_register_opcode(102, 'BUILD_TUPLE'), EFCT_DYNAMIC_EFFECT)
BUILD_LIST = _stack_effect(_register_opcode(103, 'BUILD_LIST'), EFCT_DYNAMIC_EFFECT)
BUILD_SET = _stack_effect(_register_opcode(104, 'BUILD_SET'), EFCT_DYNAMIC_EFFECT)
BUILD_MAP = _stack_effect(_register_opcode(105, 'BUILD_MAP'), EFCT_DYNAMIC_EFFECT)
LOAD_ATTR = _stack_effect(_register_opcode(106, 'LOAD_ATTR'), -1)
COMPARE_OP = _stack_effect(_register_opcode(107, 'COMPARE_OP'), -1)
IMPORT_NAME = _stack_effect(_register_opcode(108, 'IMPORT_NAME'), -1)
IMPORT_FROM = _register_opcode(109, 'IMPORT_FROM')
JUMP_FORWARD = _register_opcode(110, 'JUMP_FORWARD')
JUMP_IF_FALSE_OR_POP = _stack_effect(_register_opcode(111, 'JUMP_IF_FALSE_OR_POP'), -1)
JUMP_IF_TRUE_OR_POP = _stack_effect(_register_opcode(112, 'JUMP_IF_TRUE_OR_POP'), -1)
JUMP_ABSOLUTE = _register_opcode(113, 'JUMP_ABSOLUTE')
POP_JUMP_IF_FALSE = _stack_effect(_register_opcode(114, 'POP_JUMP_IF_FALSE'), -1)
POP_JUMP_IF_TRUE = _stack_effect(_register_opcode(115, 'POP_JUMP_IF_TRUE'), -1)
LOAD_GLOBAL = _stack_effect(_register_opcode(116, 'LOAD_GLOBAL'), 1)
SETUP_FINALLY = _register_opcode(122, 'SETUP_FINALLY')
LOAD_FAST = _stack_effect(_register_opcode(124, 'LOAD_FAST'), 1)
STORE_FAST = _stack_effect(_register_opcode(125, 'STORE_FAST'), -1)
DELETE_FAST = _register_opcode(126, 'DELETE_FAST')
RAISE_VARARGS = _stack_effect(_register_opcode(130, 'RAISE_VARARGS'), EFCT_DYNAMIC_EFFECT)
CALL_FUNCTION = _stack_effect(_register_opcode(131, 'CALL_FUNCTION'), EFCT_DYNAMIC_EFFECT)
MAKE_FUNCTION = _stack_effect(_register_opcode(132, 'MAKE_FUNCTION'), EFCT_DYNAMIC_EFFECT)
BUILD_SLICE = _stack_effect(_register_opcode(133, 'BUILD_SLICE'), EFCT_DYNAMIC_EFFECT)
LOAD_CLOSURE = _stack_effect(_register_opcode(135, 'LOAD_CLOSURE'), 1)
LOAD_DEREF = _stack_effect(_register_opcode(136, 'LOAD_DEREF'), 1)
STORE_DEREF = _stack_effect(_register_opcode(137, 'STORE_DEREF'), -1)
DELETE_DEREF = _register_opcode(138, 'DELETE_DEREF')
CALL_FUNCTION_KW = _stack_effect(_register_opcode(141, 'CALL_FUNCTION_KW'), EFCT_DYNAMIC_EFFECT)
CALL_FUNCTION_EX = _stack_effect(_register_opcode(142, 'CALL_FUNCTION_EX'), EFCT_DYNAMIC_EFFECT)
SETUP_WITH = _stack_effect(_register_opcode(143, 'SETUP_WITH'), 2)
EXTENDED_ARG = _register_opcode(144, 'EXTENDED_ARG')
LIST_APPEND = _stack_effect(_register_opcode(145, 'LIST_APPEND'), -2)
SET_ADD = _stack_effect(_register_opcode(146, 'SET_ADD'), -2)
MAP_ADD = _stack_effect(_register_opcode(147, 'MAP_ADD'), -2)
LOAD_CLASSDEREF = _stack_effect(_register_opcode(148, 'LOAD_CLASSDEREF'), 1)
BUILD_LIST_UNPACK = _stack_effect(_register_opcode(149, 'BUILD_LIST_UNPACK'), EFCT_DYNAMIC_EFFECT)
BUILD_MAP_UNPACK = _stack_effect(_register_opcode(150, 'BUILD_MAP_UNPACK'), EFCT_DYNAMIC_EFFECT)
BUILD_MAP_UNPACK_WITH_CALL = _stack_effect(_register_opcode(151, 'BUILD_MAP_UNPACK_WITH_CALL'), EFCT_DYNAMIC_EFFECT)
BUILD_TUPLE_UNPACK = _stack_effect(_register_opcode(152, 'BUILD_TUPLE_UNPACK'), EFCT_DYNAMIC_EFFECT)
BUILD_SET_UNPACK = _stack_effect(_register_opcode(153, 'BUILD_SET_UNPACK'), EFCT_DYNAMIC_EFFECT)
SETUP_ASYNC_WITH = _register_opcode(154, 'SETUP_ASYNC_WITH')
FORMAT_VALUE = _stack_effect(_register_opcode(155, 'FORMAT_VALUE'), EFCT_DYNAMIC_EFFECT)
BUILD_CONST_KEY_MAP = _stack_effect(_register_opcode(156, 'BUILD_CONST_KEY_MAP'), EFCT_DYNAMIC_EFFECT)
BUILD_STRING = _stack_effect(_register_opcode(157, 'BUILD_STRING'), EFCT_DYNAMIC_EFFECT)
BUILD_TUPLE_UNPACK_WITH_CALL = _stack_effect(_register_opcode(158, 'BUILD_TUPLE_UNPACK_WITH_CALL'), EFCT_DYNAMIC_EFFECT)
LOAD_METHOD = _stack_effect(_register_opcode(160, 'LOAD_METHOD'), 1)
CALL_METHOD = _stack_effect(_register_opcode(161, 'CALL_METHOD'), EFCT_DYNAMIC_EFFECT)
CALL_FINALLY = _stack_effect(_register_opcode(162, 'CALL_FINALLY'), 1)
POP_FINALLY = _stack_effect(_register_opcode(163, 'POP_FINALLY'), EFCT_DYNAMIC_EFFECT)


OPCODE_JUMP = (
    JUMP_ABSOLUTE,
    JUMP_FORWARD,
    JUMP_IF_TRUE_OR_POP,
    JUMP_IF_FALSE_OR_POP,
    POP_JUMP_IF_FALSE,
    POP_JUMP_IF_TRUE,
    FOR_ITER,
)

OPCODE_JUMP_REL = (
    FOR_ITER,
    JUMP_FORWARD,
    SETUP_FINALLY,
)


del _register_opcode
