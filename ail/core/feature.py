
import re

_feature_re = re.compile('//!feature<(.+)>')


FEATURE_CLASSICAL_BLOCK: int = 0x1


def _get_feature_flag(feat_str: str) -> int:
    return {
        'classical_block': FEATURE_CLASSICAL_BLOCK,
    }.get(feat_str, 0)


def parse_feature_flag(source: str) -> int:
    flags = 0

    for ln in source.split('\n'):
        if not ln:
            continue
        if ln.startswith('//!feature'):
            feat = _feature_re.findall(ln)
            if feat:
                flags |= _get_feature_flag(feat[0])
        else:
            return flags
    return flags
