# this file is for share the data between AIL RT 
# and AIL core


class _ShardData:
    find_path: str = None
    max_recursion_depth: int = None
    cwd: str = None
    base_dir: str = None
    ail_path: str = None


GLOBAL_SHARED_DATA = _ShardData()
