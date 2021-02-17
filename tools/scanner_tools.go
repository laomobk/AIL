package tools

import "unicode"

func RuneInString(r rune, str string) bool {
	for _, rn := range str {
		if r == rn {
			return true
		}
	}
	return false
}

// Chinese characters, alpha, '_' can be used as identifier.
func IsIdentifier(r rune) bool {
	return unicode.IsLetter(r) || unicode.Is(unicode.Han, r) || r == '_'
}

func IsWhite(r rune) bool {
	return unicode.IsSpace(r) || r == '\t' || r == '\r' || r == '\n'
}
