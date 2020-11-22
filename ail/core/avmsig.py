
# VM SIGNALS
# MII -> MAIN INTERPRETER INTERRUPT

MII_DO_JUMP = 0x1
MII_ERR_BREAK = 0x4
MII_ERR_POP_TO_TRY = 0x5
MII_ERR_EXIT = 0x8
MII_RETURN = 0x9

WHY_ERROR = 0x2
WHY_NORMAL = 0x3
WHY_HANDLING_ERR = 0x6
WHY_ERR_EXIT = 0x7
WHY_RETURN = 0x8


class VMInterrupt(BaseException):
    def __init__(self, signal: int = -1, handle_it: bool = True):
        super(VMInterrupt, self).__init__()
        self.signal = signal
        self.handle_it = handle_it


VM_INTERRUPT_SIGNAL = VMInterrupt()
