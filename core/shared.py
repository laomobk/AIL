# this file is for share the data between AIL RT 
# and AIL core


class _ShardData:
    find_path = None
    max_recursion_depth = None
    cwd = None
    base_dir = None


GLOBAL_SHARED_DATA = _ShardData()
