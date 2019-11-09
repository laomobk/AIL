import sys

def get_line_from_line_no(lno :int, fp :str):
    '''
    ln : 行号
    fp : 文件路径
    根据行号得到在源码的行
    '''
    if lno <= 0:
        return '<Illegal line number>'
    
    tlno = 1
    for ln in open(fp):
        if tlno == lno:
            return ln
        tlno += 1
    
    return '<NULL>'


def error_msg(line :int, msg :str, filename :str, errcode=1):
    '''
    line : 行号
    msg : 信息
    filename : 文件名
    errcode : 错误码 / 程序返回值
    '''
    sys.stderr.write('\tLine {2}: {3}\nFile: {0} :{2}, error: {1}\n'.format(
        filename, msg, line, get_line_from_line_no(line, filename)))

    sys.exit(errcode)



