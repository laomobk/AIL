package internal

import (
	"ail/tools"
)

// Abstracts

type Node interface {
	vfyNode()

	Pos() Pos
	SetPos(Pos)
}

type node struct {
	pos Pos
}

func (n *node) vfyNode() {}

func (n *node) Pos() Pos {
	return n.pos
}

func (n *node) SetPos(pos Pos) {
	n.pos = pos
}

type Expression interface {
	Node

	vfyExpr()
}

type expression struct{ node }

func (e *expression) vfyExpr() {}

type Statement interface {
	Node

	vfyStmt()
}

type statement struct{ node }

func (s *statement) vfyStmt() {}

func (s *statement) Format(depth int) string {
	return tools.FormatIndent(depth, "<Statement>")
}

// Nodes

type Block struct {
	node

	Stmts []Statement
}

type Param struct {
	node

	Name string
}

type Argument struct {
	node

	Expr    Expression
	KwValue Expression // nil if no keyword Value
	Star    Expression // unpack sequence
	KwStar  Expression // unpack map
}

// Statements

type IfStmt struct {
	statement

	IfBlock    *Block
	Condition  Expression
	ElifBlocks []IfStmt
	ElseBlock  *Block
}

type ForStmt struct {
	statement

	InitExprList   []Expression
	Condition      Expression
	UpdateExprList []Expression
	Body           *Block
}

type CatchCase struct {
	statement

	CaseExpr Expression
	Body     *Block
}

type TryStmt struct {
	statement

	TryBlock     *Block
	CatchCases   []*CatchCase // nil if no catch case
	FinallyBlock *Block       // nil if no finally block
}

type ExprStmt struct {
	statement

	Expr Expression
}

type ContinueStmt struct {
	statement
}

type BreakStmt struct {
	statement
}

type ReturnStmt struct {
	statement
}

type FuncDefStmt struct {
	statement
	expression

	Decorators []Expression // nil if no decorators
	Name       string
	ParamList  []*Param
	VarParam   string
	KwParam    string
	DefaultMap map[string]Expression
	Body       *Block
}

type ClassDefStmt struct {
	statement

	Decorators []Expression
	Name       string
	Bases      []Expression
	Body       *Block
}

// Expressions

type UnaryExpr struct {
	expression

	Expr Expression
	Op   operator
}

type BinaryExpr struct {
	expression

	LHS   Expression
	RHS   Expression
	Op    operator
	OpStr string
}

type TernaryExpr struct {
	expression

	Condition Expression
	A         Expression
	B         Expression
}

type CellExpr struct {
	expression

	Token    *Token
	NumFlags int
}

type AnonymousFunctionExpr struct {
	expression
	FuncDefStmt
}

type CallExpr struct {
	expression

	Left      Expression
	Arguments []Argument
}

type SubScriptExpr struct {
	expression

	Left  Expression
	Right Expression
}

type AccessExpr struct {
	expression

	Left Expression
	Name string
}
