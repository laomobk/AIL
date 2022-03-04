from . import shared

from .shared import GLOBAL_SHARED_DATA


class CoreCom:
    @property
    def paths(self):
        return GLOBAL_SHARED_DATA.find_path

    @property
    def cwd(self):
        return GLOBAL_SHARED_DATA.cwd

    @staticmethod
    def exit(_, code):
        if not isinstance(code, int):
            raise TypeError('exit() needs an integer.')

        import sys
        sys.exit(code)

    @property
    def argv(self):
        return shared.GLOBAL_SHARED_DATA.prog_argv


CORE_COM_OBJ = CoreCom()


def get_cc_object():
    return CORE_COM_OBJ

