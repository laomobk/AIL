
from dis import opmap as m


# NAME            VALUE
load_const = 0x01
load_local = 0x02
load_global = 0x03

call_func = 0x04
setup_while = 0x05
setup_doloop = 0x06

store_var = 0x07

compare_op = 0x08

binary_add = 0x09
binary_sub = 0x0a
binary_mult = 0x0b
binary_div = 0x0c
binary_mod = 0x0d
binary_pow = 0x0e

return_value = 0x0f
continue_loop = 0x10
break_loop = 0x11
logic_and = 0x12
logic_or = 0x13

print_value = 0x14
input_value = 0x15

jump_if_false_or_pop = 0x16
jump_if_true_or_pop = 0x18
jump_if_false = 0x19
jump_absolute = 0x17

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

init_for = 0x28
setup_for = 0x26
pop_for = 0x27

pop_loop = 0x29

set_protected = 0x2a

throw_error = 0x2b

setup_try = 0x2c
setup_catch = 0x2d
pop_catch = 0x2e
pop_try = 0x2f

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

unary_inc = 0x40
unary_dec = 0x41

store_exc = 0x42

jump_forward = 0x43

setup_finally = 0x44
pop_finally = 0x45

import_from = 0x46

push_none = 0x47

end_finally = 0x48

build_map = 0x49
build_const_key_map = 0x4a

build_class = 0x4b

inplace_add = 0x4c
inplace_sub = 0x4d
inplace_mult = 0x4e
inplace_div = 0x4f
inplace_mod = 0x50
inplace_xor = 0x51
inplace_bin_or = 0x52
inplace_lshift = 0x53
inplace_rshift = 0x54
inplace_bin_and = 0x55

jump_forward_if_false_or_pop = 0x56
jump_forward_true_or_pop = 0x57
jump_forward_if_false = 0x58
pop_jump_forward_if_true_or_pop = 0x59
pop_jump_forward_if_false_or_pop = 0x5a

unpack_sequence = 0x5b
build_tuple = 0x5c

COMP_EQ = 0
COMP_LEQ = 1
COMP_SEQ = 2
COMP_ET = 3
COMP_ST = 4
COMP_UEQ = 5
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
    binary_mult,
    binary_pow,
    binary_sub,
    binary_lshift,
    binary_rshift,
    binary_and,
    binary_or,
    binary_xor,
)


"""
_ = [
    load_const,
    load_local,
    load_global,
    call_func,
    setup_while,
    setup_doloop,
    store_var,
    compare_op,
    binary_add,
    binary_sub,
    binary_mult,
    binary_div,
    binary_mod,
    binary_pow,
    return_value,
    continue_loop,
    break_loop,
    logic_and,
    logic_or,
    print_value,
    input_value,
    jump_if_false_or_pop,
    jump_if_true_or_pop,
    jump_if_false,
    jump_absolute,
    store_function,
    load_varname,
    pop_top,
    binary_subscr,
    build_array,
    load_module,
    store_subscr,
    store_attr,
    load_attr,
    call_method,
    store_struct,
    binary_not,
    init_for,
    setup_for,
    pop_for,
    pop_loop,
    set_protected,
    throw_error,
    setup_try,
    setup_catch,
    pop_catch,
    pop_try,
    pop_jump_if_false_or_pop,
    pop_jump_if_true_or_pop,
    unary_negative,
    bind_function,
    import_name,
    load_variable,
    binary_lshift,
    binary_rshift,
    binary_and,
    binary_or,
    binary_xor,
    unary_invert,
    make_function,
    call_func_ex,
    join_array,
    delete_var,
    unary_inc,
    unary_dec,
    store_exc,
    jump_forward,
    setup_finally,
    pop_finally,
    import_from,
    push_none,
    end_finally,
    build_map,
    build_const_key_map,
    build_class,
    inplace_add,
    inplace_sub,
    inplace_mult,
    inplace_div,
    inplace_mod,
    inplace_xor,
    inplace_bin_or,
    inplace_lshift,
    inplace_rshift,
    inplace_bin_and,
    jump_forward_if_false_or_pop,
    jump_forward_true_or_pop,
    jump_forward_if_false,
    pop_jump_forward_if_true_or_pop,
    pop_jump_forward_if_false_or_pop,
]
"""
