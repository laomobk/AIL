from . import aobjects as objs


class Frame:
    __slots__ = ('code', 'stack', 'varnames', 'consts',
                 'variable', 'break_stack', 'temp_env_stack',
                 'try_stack', '_marked_opcounter', '_latest_call_opcounter',
                 'closure_outer', 'globals', 'lineno')

    def __init__(self, code: objs.AILCodeObject = None, varnames: list = None,
                 consts: list = None, globals: dict = None,
                 closure_outer_variable: list = None):
        self.code: objs.AILCodeObject = code
        self.stack = []
        self.varnames = varnames if varnames else list()
        self.consts = consts if consts else list()
        self.variable = globals if globals else dict()
        self.break_stack = []
        self.temp_env_stack = []
        self.try_stack = []
        self.lineno = 0

        # for closure
        self.closure_outer = closure_outer_variable \
            if closure_outer_variable is not None \
            else list()

        self._marked_opcounter = 0
        self._latest_call_opcounter = 0

    def __str__(self):
        return '<Frame object for code object \'%s\'>' % self.code.name

    __repr__ = __str__
