
from .aobjects import AILObject


class Namespace:
    def __init__(self, 
                 ns_name: str, 
                 ns_dict: dict, 
                 ns_last: 'Namespace' = None):
        self.ns_name = ns_name
        self.ns_dict = ns_dict
        self.ns_last = ns_last

    def get(self, name: str) -> AILObject:
        v = self.ns_dict.get(name, None)
        if v is None:
            last = self.ns_last
            if last is None:
                return None
            return last.get(name)
        return v

    def set(self, name: str, value: AILObject):
        self.ns_dict[name] = value

