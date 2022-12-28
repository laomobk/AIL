# AIL 3.0 Lumine

AIL 3.0 于 2022 年 6 月 11 日开始开发，以下是目前为止 AIL 3.0 的更新内容：

## == 主要更新 ==

### 一、自编译模式 Self Compilation

自编译模式将使用 AIL 的编译器编译 AIL 源码以输出 Python 字节码。相比之下，本地编译模式突破了 Python 的语法限制，使得 AIL 可以进一步优化如匿名函数，match 表达式等特性，大大提高了运行效率。

例如，匿名函数在 AIL 3.0 版本中得到优化：

```swift
// code1.ail

mapwith((i, x) -> {
    print '%s -> %s' % (i, x);
}, range(10, 20));
```

在 AIL 2.3 版本中，由于 Python 语法书限制，code1.ail 将会被编译成下面的字节码：

```python
  4           0 LOAD_CONST               0 (<code object <anonymous 167318953876-4> at 0x0000026F4FCAFF50, file "<test>", line 4>)
              2 LOAD_CONST               1 ('<anonymous 167318953876-4>')
              4 MAKE_FUNCTION            0
              6 STORE_NAME               0 (<anonymous 167318953876-4>)

  2           8 LOAD_NAME                1 (mapwith)
             10 LOAD_NAME                0 (<anonymous 167318953876-4>)

  4          12 LOAD_NAME                2 (range)
             14 LOAD_CONST               2 (10)
             16 LOAD_CONST               3 (20)
             18 CALL_FUNCTION            2

  2          20 CALL_FUNCTION            2
             22 POP_TOP
             24 LOAD_CONST               4 (None)
             26 RETURN_VALUE

Disassembly of <code object <anonymous 167318953876-4> at 0x0000026F4FCAFF50, file "<test>", line 4>:
  3           0 LOAD_GLOBAL              0 (print)
              2 LOAD_CONST               1 ('%s -> %s')
              4 LOAD_FAST                0 (i)
              6 LOAD_FAST                1 (x)

  1           8 BUILD_TUPLE              2

  3          10 BINARY_MODULO
             12 CALL_FUNCTION            1
             14 POP_TOP
             16 LOAD_CONST               0 (None)
             18 RETURN_VALUE
```

可以发现，传入 `mapwith` 的匿名函数被编译成为了一条隐式赋值语句，而这个匿名函数在运行时中并不是临时的，当使用完此匿名函数之后，此函数仍然会留在名称空间中。而使用 AIL 3 则不会出现这样的问题：

```python
  2           0 LOAD_NAME                0 (mapwith)

  4           2 LOAD_CONST               0 (<code object <anonymous function> at 0x000001EDD318D240, file "<unknown>", line 3>)
              4 LOAD_CONST               1 ('<anonymous function>')
              6 MAKE_FUNCTION            0
              8 LOAD_NAME                1 (range)
             10 LOAD_CONST               2 (10)
             12 LOAD_CONST               3 (20)
             14 CALL_FUNCTION            2
             16 CALL_FUNCTION            2
             18 POP_TOP
             20 LOAD_CONST               4 (None)
             22 RETURN_VALUE

Disassembly of <code object <anonymous function> at 0x000001EDD318D240, file "<unknown>", line 3>:
  3           0 LOAD_GLOBAL              0 (print)
              2 LOAD_CONST               0 ('%s -> %s')
              4 LOAD_FAST                0 (i)
              6 LOAD_FAST                1 (x)
              8 BUILD_TUPLE              2
             10 BINARY_MODULO
             12 CALL_FUNCTION            1
             14 POP_TOP
             16 LOAD_CONST               1 (None)
             18 RETURN_VALUE
```

可以发现，在 AIL 3 中，匿名函数的定义仅仅是被编译成了一条 `MAKE_FUNCTION` 指令，此函数仅仅是停留在栈上，当需要使用此函数时，它就被从栈中弹出，不会对名称空间造成任何影响。


### 二、PyASM 支持

PyASM 允许用户直接在 AIL 程序中插入 Python 字节码指令（目前仅支持部分指令）：

```
print % (
    load_const('hello ')
    load_const('Klee')
    binary_add
)
```

```
%load_const ('last');
print %load_const('hello'), %load_const('Klee');
x = %();
print %load_const('x ='), %load_name('x')
```

PyASM 块是*一个伪表达式*，即它可以在语法上可以作为表达式放入如函数参数，条件表达式的位置，但是在运行时**不一定会返回值**。

*但在多数情况下，如果在被作为表达式的情况下没有返回值，AIL 将会崩溃。*

*PyASM 表达式将会被直接嵌入到输出的 Python 字节码中，为了使得程序不崩溃，请在使用 PyASM 前对字节码有一定的认识*


## == 主要变更 ==

### 二、Python 版本需求

由于本地编译模式的加入，AIL 3 将 **仅支持 Python 3.8.x** 版本，使用其他版本的 Python 将出现不稳定的情况。

