# unsafe/thread

from threading import Thread, Lock

from ail.core import alock
from ail.core.aobjects import get_state, convert_to_ail_object
from ail.core.avm import Interpreter


_thread_count = 0


def thread_run(func):
    """
    run(func: Callable)

    call function asynchronously.
    """
    global _thread_count

    alock.GLOBAL_INTERPRETER_LOCK = Lock()

    interpreter = get_state().global_interpreter

    thread = Thread(target=interpreter.call_function, args=(func, 0, []))
    thread.setDaemon(0)
    thread.start()


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'run': convert_to_ail_object(thread_run),
}
