package ail

import (
	"fmt"
)

type Pos struct {
	line, col int
}

func (p *Pos) String() string {
	return fmt.Sprintf("(Line: %d Col: %d)", p.line, p.col)
}

func (p *Pos) Line() int {
	return p.line
}

func (p *Pos) Col() int {
	return p.col
}
