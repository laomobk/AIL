begin

// I LOVE YOU...


_y_decr = fnum(0.1)
_x_incr = fnum(0.05)
_zero = fnum(0)
_y_comp = fnum(-1.5)
_x_comp = fnum(1.5)
_one = fnum(1)


for (y = fnum(1.5), ln = ''; y > _y_comp; y = y - _y_decr, ln = '') then
    for (x = fnum(-1.5); x < _x_comp; x = x + _x_incr) then
        a = x * x + y * y - _one

        if a * a * a - x * x * y * y * y <= _zero then
            ln = ln + '@'
        else
            ln = ln + ' '
        endif
    end
    print ln
end

end
