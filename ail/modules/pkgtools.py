
from ail.py_runtime.exceptions import AILImportError, AILModuleNotFoundError
from ail.py_runtime.objects import AILImporter

_AIL_PYC_MODULE_ = True


def get_path(module_name: str):
    return AILImporter.get_path(module_name, None)


def get_source(path: str):
    return AILImporter.get_source(path)


def get_namespace(source: str, path: str) -> dict:
    try:
        return AILImporter.get_namespace(path, source)
    except (AILImportError, AILModuleNotFoundError):
        return None


_AIL_NAMESPACE_ = {
    'get_path': get_path,
    'get_source': get_source,
    'get_namespace': get_namespace,
}

