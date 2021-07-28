
import builtins as _builtins

from ail.core.objects import (
    AILModule as _AILModule,
)


_readline_available = False

try:
    import readline
    _readline_available = True
except ImportError:
    pass


class Completer:
    def __init__(self, namespace: dict):
        self.namespace = namespace
        self.matches = []

    def complete(self, text: str, state: int) -> str:
        if not _readline_available:
            return '\t'

        namespace = self.namespace

        if not text.strip():
            if state == 0:
                readline.insert_text('\t')
                readline.redisplay()
                return ''
            else:
                return None

        if state == 0:
            if '.' in text:
                self.matches = self.match_attr(text)
            else:
                self.matches = self.match_name(text)

        try:
            return self.matches[state]
        except IndexError:
            return None

    def __check_callable_prefix(self, word, obj) -> str:
        return ('%s(' % word) if callable(obj) else word

    def match_name(self, text: str):
        from ..core.aparser import _keywords

        ns = self.namespace
        matches = []
        n = len(text)

        for word in _keywords:
            if word not in matches:
                if word[:n] == text:
                    matches.append(word)

        for word in ns.keys():
            if '::' in word:
                continue

            if word[:n] == text:
                try:
                    word = self.__check_callable_prefix(word, ns[word])
                except Exception:
                    pass
                matches.append(word)

        for word in dir(_builtins):
            if word not in matches:
                if word[:n] == text:
                    try:
                        word = self.__check_callable_prefix(
                                word, getattr(_builtins, word))
                    except Exception:
                        pass
                    matches.append(word)

        return matches

    def match_attr(self, text: str):
        import re
        m = re.match(r"(\w+(\.\w+)*)\.(\w*)", text)
        if not m:
            return []
        
        expr, attr = m.group(1, 3)

        try:
            this = eval(expr, self.namespace)
        except Exception:
            return []

        words = []

        if isinstance(this, _AILModule):
            try:
                words = set(this._module_globals.keys())
            except AttributeError:
                words = set(dir(this)) 
        else:
            words = set(dir(this))

        n = len(attr)
        
        matches = []

        show_prefix = attr[:1] == '_'
        
        for word in words:
            if '::' in word:
                continue

            if word[:1] == '_' and not show_prefix:
                continue
            if word[:n] == attr:
                try:
                    word = self.__check_callable_prefix(word, getattr(this, word))
                except Exception:
                    pass

                matches.append('%s.%s' % (expr, word))
        
        matches.sort()
        return matches


_AIL_PYC_MODULE_ = True
_AIL_NAMESPACE_ = {'Completer': Completer}

