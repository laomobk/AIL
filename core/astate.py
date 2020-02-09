from core import agc


class InterpreterState:
    def __init__(self):
        self.frame_stack :list = []
        self.gc : agc.GC = None


MAIN_INTERPRETER_STATE = InterpreterState()
