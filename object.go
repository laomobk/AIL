package ail

type Object struct {
	objType *TypeObject
}

type TypeObject struct {
	typeName string
	bases    []*TypeObject

	typeDict map[string]*Object

	funcNew  func(*TypeObject, *Object) *Object
	funcInit func(*Object, *Object) *Object
	funcStr  func(*Object) *Object
	funcRepr func(*Object) *Object
	funcDel  func(*Object) *Object
}
