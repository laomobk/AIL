# PyASM

**只支持 AIL 3.0 及以上的版本**

PyASM 是 AIL 中的一个较为高级的特性，它允许开发者直接在 AIL 程序中嵌入 cpython 字节码。由于 PyASM 在编译期间并不会进行任何的语义分析，在 PyASM 中对所有变量的引用和赋值均不会追踪。同时，由于没有栈分析，错误的 PyASM 操作可能会导致程序的崩溃。


## cpython 字节码基本介绍

想要使用 PyASM，必须要对 cpython 字节码有一定的了解。cpython 字节码是 Python 代码经过 cpython 编译器生成的字节指令序列，最终 cpython 虚拟机将读取并执行这些指令序列，这也是 Python 程序执行的流程（对于 cpython 而言）。

cpython 的虚拟机是基于栈的虚拟机，自然而然地，对应的字节码也是基于栈进行操作的。在 cpython 程序执行的过程中，有十分频繁的栈操作。所以说，在编写 PyASM 的过程中，要时刻注意栈的状态。

### 简单认识 cpython 字节码指令

下面是一个简单的 AIL 代码段：

```python
greeting = 'Hello %s!';
who = 'Klee';
print greeting % who;
```

这段代码对应的字节码如下：

```
LOAD_CONST      0
STORE_NAME      0
LOAD_CONST      1
STORE_NAME      1
LOAD_GLOBAL     2
LOAD_NAME       0
LOAD_NAME       1
BINARY_MODULO
CALL_FUNCTION   1
POP_TOP
```

这是一段非常简单的字节码指令序列，它是线性的，全程没有控制流的影响。

