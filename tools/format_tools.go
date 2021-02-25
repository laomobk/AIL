package tools

import (
	"fmt"
	"reflect"
	"strings"
)

var Indent = "  "

func FormatIndent(depth int, s string) string {
	return fmt.Sprintf("%s%s", strings.Repeat(Indent, depth), s)
}

func formatStruct(depth int, v reflect.Value) string {
	t := v.Type()

	fieldStrings := make([]string, 0)

	fieldStrings = append(fieldStrings,
		FormatIndent(depth,
			fmt.Sprintf(
				"%s %v {", t.Kind().String(), t.Name())))

	for i := 0; i < t.NumField(); i++ {
		field := t.Field(i)
		fieldName := field.Name
		fieldValue := v.FieldByName(fieldName)
		fieldStrings = append(fieldStrings, FormatIndent(depth+1, fieldName)+":")
		fieldStrings = append(fieldStrings, formatValue(depth+2, fieldValue))
	}

	fieldStrings = append(fieldStrings, FormatIndent(depth, "}"))

	return strings.Join(fieldStrings, "\n")
}

func FormatStruct(s interface{}) string {
	return formatStruct(0, reflect.ValueOf(s))
}

func formatSlice(depth int, v reflect.Value) string {
	buf := make([]string, 0)

	buf = append(buf, FormatIndent(depth, "["))

	for i := 0; i < v.Len(); i++ {
		elemStr := formatValue(depth+1, v.Index(i))
		buf = append(buf, FormatIndent(depth, fmt.Sprintf("(index %d)", i)))
		buf = append(buf, elemStr)
	}

	buf = append(buf, FormatIndent(depth, "]"))

	return strings.Join(buf, "\n")
}

func FormatSlice(s interface{}) string {
	return formatSlice(0, reflect.ValueOf(s))
}

func formatValue(depth int, v reflect.Value) string {
	switch v.Kind() {

	case reflect.Struct:
		return formatStruct(depth, v)
	case reflect.String:
		return FormatIndent(depth,
			fmt.Sprintf("\"%v\"", v.String()))
	case reflect.Int, reflect.Int8, reflect.Int16, reflect.Int32, reflect.Int64:
		return FormatIndent(depth, fmt.Sprintf("%v", v.Int()))
	case reflect.Uint, reflect.Uint8, reflect.Uint16, reflect.Uint32, reflect.Uint64:
		return FormatIndent(depth, fmt.Sprintf("%v", v.Uint()))
	case reflect.Slice, reflect.Array:
		return formatSlice(depth, v)
	case reflect.Interface:
		return fmt.Sprintf(
			"%s\n%s",
			FormatIndent(depth, fmt.Sprintf(
				"[interface %v]", v.Type().Name())),
			formatValue(depth, v.Elem()))
	case reflect.Uintptr, reflect.Ptr:
		return fmt.Sprintf(
			"%s\n%s",
			FormatIndent(depth, "(pointer)"),
			formatValue(depth, v.Elem()))
	case reflect.Invalid:
		return "<nil>"

	}
	return FormatIndent(depth, fmt.Sprintf("<unsupported kind: %v>", v.Kind()))
}

func FormatValue(t interface{}) string {
	return formatValue(0, reflect.ValueOf(t))
}

func PrintFotmatValue(t interface{}) {
	fmt.Println(FormatValue(t))
}
