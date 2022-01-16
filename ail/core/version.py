from os.path import exists, join
from .._config import CORE_PATH


AIL_MAIN_VERSION = 2
AIL_SUB_VERSION = [2]
AIL_VERSION_STATE = 'alpha 0'
AIL_VERSION_NAME = 'Klee'

AIL_VERSION = '%s.%s%s' % (
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

AIL_VERSION_NUMBER = 727


AIL_COPYRIGHT = '2021 Chenhongbo'

AIL_INSTALL_TIME = -1
