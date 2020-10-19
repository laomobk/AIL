# NAME            VALUE
load_const      = 0x01
load_local      = 0x02
load_global     = 0x03

call_func       = 0x04
setup_while     = 0x05
setup_doloop    = 0x06

store_var       = 0x07

compare_op      = 0x08

binary_add      = 0x09
binary_sub      = 0x0a
binary_muit     = 0x0b
binary_div      = 0x0c
binary_mod      = 0x0d
binary_pow      = 0x0e

return_value    = 0x0f
continue_loop   = 0x10
break_loop      = 0x11
logic_and       = 0x12
logic_or        = 0x13

print_value     = 0x14
input_value     = 0x15

jump_if_false_or_pop   = 0x16
jump_if_true_or_pop = 0x18
jump_if_false = 0x19
jump_absolute   = 0x17

store_function = 0x1a

load_varname = 0x1b

pop_top = 0x1c

binary_subscr = 0x1d
build_array = 0x1e

load_module = 0x1f

store_subscr = 0x20
store_attr = 0x21
load_attr = 0x22

call_method = 0x23

store_struct = 0x24

binary_not = 0x25

init_for  = 0x28
setup_for = 0x26
clean_for = 0x27

clean_loop = 0x29

set_protected = 0x2a

throw_error = 0x2b

setup_try = 0x2c
setup_catch = 0x2d
clean_catch = 0x2e
clean_try = 0x2f

pop_jump_if_false_or_pop = 0x30
pop_jump_if_true_or_pop = 0x31

unary_negative = 0x32
bind_function = 0x33

import_name = 0x34

load_variable = 0x35
binary_lshift = 0x36
binary_rshift = 0x37
binary_and = 0x38
binary_or = 0x39
binary_xor = 0x3a

unary_invert = 0x3b

make_function = 0x3c

call_func_ex = 0x3d
join_array = 0x3e

delete_var = 0x3f

COMP_EQ     = 0
COMP_LEQ    = 1
COMP_SEQ    = 2
COMP_ET     = 3
COMP_ST     = 4
COMP_UEQ    = 5
COMPARE_OPERATORS = (
    '==',
    '>=',
    '<=',
    '>',
    '<',
    '!=',
)

BINARY_OPS = (
    binary_add,
    binary_div,
    binary_mod,
    binary_muit,
    binary_pow,
    binary_sub,
    binary_lshift,
    binary_rshift,
    binary_and,
    binary_or,
    binary_xor,
)
