from pprint import pprint
from sys import _getframe
from threading import Thread
from time import sleep
from typing import List
from types import FrameType


def get_frame() -> List[FrameType]:
    f_list = []
    cur_f = _getframe()  # type: FrameType
    cur_f = cur_f.f_back
    f_list.append(cur_f)

    while cur_f is not None:
        cur_f = cur_f.f_back
        f_list.append(cur_f)

    return f_list


def f():
    f = get_frame()
    pprint(f)


t = Thread(target=f)
t.start()
sleep(0.01)
f = get_frame()
pprint(f)