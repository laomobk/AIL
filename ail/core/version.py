# the version info of AIL
#
# -- the AIL version number:
#
# 2.1   Leopard     726     2021.5 - 2022.1
# 2.2   Klee        727     2022.1 - 2022.3
# 2.3   Diona       728     2022.3 - now
#

from os.path import exists, join
from .._config import CORE_PATH


AIL_MAIN_VERSION = 2
AIL_SUB_VERSION = [3]
AIL_VERSION_STATE = 'alpha 3'
AIL_VERSION_NAME = 'Diona'

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

AIL_VERSION_NUMBER = 728


AIL_COPYRIGHT = '2022 Chenhongbo'

AIL_INSTALL_TIME = -1
