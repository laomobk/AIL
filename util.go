package ail

func runeInString(r rune, str string) bool {
	for _, rn := range []rune(str) {
		if r == rn {
			return true
		}
	}
	return false
}
