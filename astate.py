import aobjects as objs

class InterpreterState:
    def __init__(self):
        self.now_codeobj :objs.AILCodeObject = None
        self.frame_stack :list = []
        self.gc :GC = None
