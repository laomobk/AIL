

def set_doc(obj, doc_str: str):
    if not isinstance(doc_str, str):
        return

    obj['__doc__'] = doc_str
