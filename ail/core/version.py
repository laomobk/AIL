from os.path import exists, join
from .._config import CORE_PATH


AIL_MAIN_VERSION = 2
AIL_SUB_VERSION = [1]
AIL_VERSION_STATE = 'alpha 2'
AIL_VERSION = '%s.%s %s' % (AIL_MAIN_VERSION,
                            '.'.join([str(v) for v in AIL_SUB_VERSION]),
                            AIL_VERSION_STATE)


AIL_COPYRIGHT = '2021 Chenhongbo'

AIL_INSTALL_TIME = -1
