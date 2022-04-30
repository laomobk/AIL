
# Shadow Assign 语句

shadow assign 语句能够在定义变量时，对将要定义的变量进行跨域搜寻操作。最直接的效果就在于能在函数体内使用在 global 域中的变量来定义一个与其同名的变量。

## 语法

shadow assign 语句的语法如下：

```
NAME ':=' expr ';'
```

## 跨域搜寻

```go
a = 1;

func f() {
    a = a + 1;  // exception !!
}

f();
```

对于上面的程序来说，在运行至第四行的时候，会抛出一个这样的异常：

```python
UnboundLocalError: local variable 'a' referenced before assignment
```

而使用 shadow assign 则不会出现这样的问题：

```go
a = 1;

func f() {
    a := a + 1;  // the value of a is 2
}

f();
```

原因在于，shadow assign 会对右部中的 `a` 变量采取特殊的搜寻模式，但并不是对右部所有的变量使用这种搜寻模式，如 `a := a + b` ，其中 `b` 变量的搜寻则按照普通的搜寻模式。

这一特殊的搜寻模式是指按照 **从 global 域到 local 域的顺序搜寻变量** ，也就是说，当 local 域与 global 域同时存在着满足需求的变量时，会优先选择 global 域的值：

```go
a = 1;

func f() {
    a = 2;
    a := a + 1;  // the value of a is 2
}
```

## 异常的抛出

当 shadow assign 无法找到所需的变量时，会抛出 `NameError`：

```python
>> a := a + 1
Traceback (most recent call last):
  File "<shell>", line 1, in <module>
NameError: name 'a' is not defined in neither global nor local scope
```

## 性能

实际上，shadow assign 语句对性能的影响比较大，相比于普通的 assign 语句，shadow assign 需要更复杂的过程，因此，在实际开发中，应尽量避免使用 shadow assign 语句，尽量仅将其作为揽入全局变量的一个工具，这也是 shadow assign 语句设计的初衷：

```go
a = get_data(TIME);

func f() {
    a := a;
}
```

