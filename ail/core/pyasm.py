
from typing import Dict

from . import pyopcode as _o


class OpcodeRecord:
    def __init__(self, code: int, arg_types: int):
        self.code = code
        self.arg_types = arg_types


def _reg_pyasm_opcode(opcode, arg_types: int):
    return (
        _o.OPCODE_TO_NAME_MAP[opcode],
        OpcodeRecord(
            opcode,
            arg_types,
        )
    )


ARG_NONE = 1
ARG_NUMBER = 0x2
ARG_INT = 0x4
ARG_STRING = 0x8
ARG_OBJECT = 0x10
ARG_FLOAT = 0x20

SUPPORTED_OPCODES: Dict[str, OpcodeRecord] = {
    k: v for k, v in (
        _reg_pyasm_opcode(_o.BINARY_ADD, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_AND, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_FLOOR_DIVIDE, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_LSHIFT, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_MATRIX_MULTIPLY, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_MODULO, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_MULTIPLY, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_OR, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_POWER, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_RSHIFT, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_SUBSCR, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_SUBTRACT, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_TRUE_DIVIDE, ARG_NONE),
        _reg_pyasm_opcode(_o.BINARY_XOR, ARG_NONE),
        _reg_pyasm_opcode(_o.LOAD_CONST, ARG_NUMBER | ARG_STRING)
    )
}

