package test_data

import (
	"ail/cmd/ail/internal"
	"ail/tools"
	"fmt"
	"testing"
)

func TestBlockAST(test *testing.T) {
	b := new(internal.Block)
	s := make([]internal.Statement, 0)

	s = append(s, &internal.ExprStmt{
		Expr: &internal.BinaryExpr{
			LHS: &internal.CellExpr{},
			RHS: &internal.CellExpr{},
		},
	})

	b.Stmts = s

	fmt.Println(tools.FormatValue(b))
}
