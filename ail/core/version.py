# the version info of AIL
#
# -- the AIL version number:
#
# 2.1   Leopard     726     2021.5 - 2022.1
# 2.2   Klee        727     2022.1 - 2022.3
# 2.3   Diona       728     2022.3 - 2022.6
# 3.0   Lumine      729     2022.6 - now
#

from os.path import exists, join
from .._config import CORE_PATH


AIL_MAIN_VERSION = 3
AIL_SUB_VERSION = [0]
AIL_VERSION_STATE = 'alpha 1'
AIL_VERSION_NAME = 'Lumine'

AIL_VERSION = '%s.%s %s' % (
    AIL_MAIN_VERSION,
    '.'.join([str(v) for v in AIL_SUB_VERSION]),
    AIL_VERSION_STATE
)

AIL_VERSION_FULL_STRING = '%s.%s%s%s' % (
    AIL_MAIN_VERSION,
    '.'.join((str(v) for v in AIL_SUB_VERSION)),
    (' %s ' % AIL_VERSION_NAME) if AIL_VERSION_NAME else '',
    ('%s' % AIL_VERSION_STATE) if AIL_VERSION_STATE else '',

)

AIL_VERSION_NUMBER = 729


AIL_COPYRIGHT = '2022 Chenhongbo'

AIL_INSTALL_TIME = -1


def _easy_checker_constructer(ver: float, cmp_func):
    return lambda target: cmp_func(ver, target)


PY_VERSION_REQUIRE = (
    '==', 3, 8,
    _easy_checker_constructer(3.8, float.__eq__)
)

