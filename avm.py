# virtual machine for AIL

import aobjects as objs
from typing import List
from .agc import GC
from .astate import InterpreterState
import threading


# GLOBAL SETTINGS
REFERENCE_LIMIT = 8192


class Frame:
    def __init__(self):
        self.stack = []
        self.varnames = []
        self.consts = []
        self.variable = {}


class Interpreter:
    def __init__(self, cobj :objs.AILCodeObject):
        self.__now_state = InterpreterState()  # init state
        self.__gc = GC(REFERENCE_LIMIT)  # each interpreterhas one GC
        self.__now_state.gc = self.__gc

    @property
    def __tof(self) -> Frame:
        return self.__now_state.frame_stack[-1]   \
            if self.__now_state.frame_stack   \
            else None

    @property
    def __tos(self) -> objs.AILBaseObject:
        return self.__tof.stack[-1]   \
            if self.__tof.stack   \
            else None

    @property
    def __stack(self) -> List[objs.AILBaseObject]:
        return self.__tof.stack