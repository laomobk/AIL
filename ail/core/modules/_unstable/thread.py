# unsafe/thread

from threading import Thread, Lock

from ail.core import alock
from ail.core.aobjects import get_state, convert_to_ail_object
from ail.core.athread import ThreadState, THREAD_SCHEDULER


_thread_count = 0


def thread_run(func):
    """
    run(func: Callable)

    call function asynchronously.
    """
    global _thread_count

    m_state = get_state()

    interpreter = m_state.global_interpreter

    if alock.GLOBAL_INTERPRETER_LOCK is None:
        alock.GLOBAL_INTERPRETER_LOCK = Lock()
        interpreter.main_lock = Lock()
        main_thread_state = ThreadState(m_state.frame_stack, None, interpreter.main_lock)
        main_thread_state.op_counter = interpreter.op_counter
        THREAD_SCHEDULER.add_thread(main_thread_state)
        THREAD_SCHEDULER.now_running_thread = main_thread_state

    arg = [func, 0, []]
    thread = Thread(target=interpreter.call_function_async, args=arg)

    t_state = ThreadState(m_state.frame_stack.copy(), thread)
    t_count = THREAD_SCHEDULER.add_thread(t_state)
    arg.insert(0, t_count)
    arg.insert(1, t_state)

    # thread.setDaemon(True)
    thread.start()
    THREAD_SCHEDULER.schedule()


_IS_AIL_MODULE_ = True
_AIL_NAMESPACE_ = {
    'run': convert_to_ail_object(thread_run),
}
