# virtual machine for AIL

import aobjects as objs
from typing import List

class Frame:
    def __init__(self):
        self.stack = []
        self.varnames = []
        self.consts = []
        self.variable = {}


class InterpreterState:
    def __init__(self):
        self.now_codeobj :objs.AILCodeObject = None
        self.frame_stack :List[Frame] = []


class Interpreter:
    def __init__(self, cobj :objs.AILCodeObject):
        self.__now_state = InterpreterState()  # init state

    @property
    def __tof(self) -> Frame:
        return self.__now_state.frame_stack[-1]   \
            if self.__now_state.frame_stack   \
            else None

    @property
    def __tos(self):
        return self.__tof.stack[-1]   \
            if self.__tof.stack   \
            else None