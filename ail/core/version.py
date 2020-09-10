
AIL_MAIN_VERSION = 1
AIL_SUB_VERSION = [1]
AIL_VERSION_STATE = 'build'
AIL_VERSION = '%s.%s %s' % (AIL_MAIN_VERSION,
                            '.'.join([str(v) for v in AIL_SUB_VERSION]),
                            AIL_VERSION_STATE)
