# 本地编译模式

> Version:
>     2022.8.10


## 介绍

本地编译模式使用 AIL 的编译器编译 AIL 代码，直接输出 Python 字节码。

在 AIL 2 中使用 `委托编译模式` 来执行 AIL 代码，过程如下：

```

[AIL code]
    |
    v
  [alex]  --> (token stream)
                   |
                   |
 [aparser] <--------
     |
     v
 (AIL AST)
     |
     v
[converter]
     |
     v
(Python AST) --> [Python compiler] --> (Python code object)
                                                |
                                                v
                                            (Python VM)


```

可以看出，委托编译模式委托了 Python 的编译器来编译得到代码对象。由于 Python 的编译器需要使用 Python AST 来进行编译，所以说还需要使用 `Converter` 来将 AIL AST 转换成为 Python AST，因此 AIL 的特性受到 Python 语法的限制。

在 AIL 3 中将使用 `本地编译模式` 来执行 AIL 代码，过程如下：

```

[AIL code]
    |
    v
  [alex]  --> (token stream)
                   |
                   |
 [aparser] <--------
     |
     v
 (AIL AST)
     |
     v
[AIL Compiler] --> (Python code object)
                            |
                            v
                       (Python VM)


```

当使用 AIL Compiler 之后，将可以根据特性需求，自行生成对应的字节码序列，而不是将特性转化为等效的 Python AST，因为即使转换成等效代码，其生成也不是最便捷的。

如函数中的 `a := a` 语句在 AIL 2 中被编译成一个复杂的函数调用和赋值的过程：

```
  0 LOAD_GLOBAL              0 (ail::get_var)
  2 LOAD_CONST               1 ('a')
  4 LOAD_GLOBAL              1 (py::globals)
  6 CALL_FUNCTION            0
  8 LOAD_GLOBAL              2 (py::locals)
 10 CALL_FUNCTION            0
 12 CALL_FUNCTION            3
 14 STORE_FAST               0 (a)
 16 LOAD_FAST                0 (a)
 18 STORE_FAST               0 (a)
 20 LOAD_CONST               0 (None)
 22 RETURN_VALUE
```

而在 AIL 3 版本中，将被直接编译为：

```
  0 LOAD_GLOBAL              0 (a)
  2 STORE_FAST               0 (a)
```

大大提高了运行效率。

