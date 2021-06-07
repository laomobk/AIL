# AIL 的 Python 等效代码参考

AIL 的转换器把 AIL 代码转换成 Python 代码执行，为了更好的学习 AIL ，有必要了解其中的等效关系

*阅读提示：当两个代码块叠一起时，通常上面是 AIL 代码，下面是等效 Python 代码*

## input 语句

Python 不能直接实现类似 AIL 的 input 语句，因此 AIL 的 input 语句是转换成 `__ail_input__` 的调用执行的：

```python
input 'value: ';
```

```python
__ail_input__('value: ', 0)
```

当有变量赋值操作时：

```python
input 'value: ', value;
```

```python
value = __ail_input__('value: ', 1)
```

其中，等效关系如下：

```python
input prompt [, var1 [, var2 [...]]];
```

```python
[[var1 [, var2 [...]]] = ] __ail_input__(prompt, value_count)
```

__ail_input\_\_ 实现：

```python
def ail_input(prompt: str, value_count: int):
    m = input(prompt)
    if value_count == 1:
        return m
    if value_count == 0:
        return None

    vals = m.split(maxsplit=value_count)
    if len(vals) < value_count:
        raise ValueError('no enough value to split')

    return vals
```



## print 语句

AIL 直接 print 语句转换为 `print` 函数的调用

```python
print msg1 [, msg2 [...]];
```

```python
print(msg1 [, msg2 [...]])
```



## for 与 while 语句

### 经典 for 语句

经典 3 段式 for 语句会被编译成 while 语句，**其中，`init` 部分语句会被放在 while 语句前，`test` 被作为 while 语句的 `test` ，for 的循环体在 while 语句块内由 try-finally 包裹，finally 块内是 `update` 部分：**  

```go
for init; test; update { ... }
```

```python
init  # 可能有多行
while test:
    try:
        ...
    finally:
        update  # 可能有多行
```

### forever 语句

AIL 直接将 forever 语句编译为：

```python
while True:
    ...
```

### 单条件 for 语句与while语句

单条件 for 语句会被直接转换成 while 语句处理，这里不多赘述。



## do 语句

同 for 语句，do 语句也会被编译成 while 语句，**其中， while 语句的 `test` 部分永远是 True，do 循环体在 while 语句块中由 try-finally 包裹，finally 块内是一个  if 语句，if 语句的 `test` 部分为 do 语句的 `test` ，若 `test` 成立，则跳出循环。 **  

```
do {
    ...
} loop until test;
```

```python
while True:
    try:
        ...
    finally:
        if test:
            break
```



## 匿名函数和 lambda 函数

AIL 具有与 Python 相同和不同的 lambda 函数类型，还有匿名函数的支持，下面对不同的情况进行讲解。

### 标准 lambda 函数

标准 lambda 函数与 λ 演算中的 λ 类似，只有变量与 lambda 项。Python 原生支持这样的 lambda 表达式，所以 AIL 直接将此类 lambda 表达式转换成 Python 的 lambda 表达式。

```
([params]) -> expression
```

```python
lambda [params]: expression
```

### 块 lambda 函数与匿名函数

块 lambda 函数与匿名函数的转换结果是一样的。因为 Python 的语法树不支持块匿名函数的操作，因此，AIL 会将匿名函数转换为**两条语句**：

```swift
f = func ([params]) { ... }  // or: f = ([params]) -> { ... }
```

```
def <anonymous 2838447>():
    pass
f = <anonymous 2838447>
```

其中，anonymous 后接的数字是为了防止出现冲突现象。第二条是匿名函数所处的语句，匿名函数的位置被替换成生成的匿名函数的名字，在上面的例子是： `<anonymous 2838447>`

## import 语句与 load 语句

AIL 将 import 语句与 load 语句都转换为对 `__ail_import__` 函数的调用，但是两者在调用的参数上有区别。

这里给出 `__ail_import__` 的函数签名：

```python
def ail_import(
        mode: int, name: str, namespace: dict, 
        alias: str=None, members: List[str]=None):
    ...
```

### import 语句

```python
import [alias] path [(members...)]
```

```python
__ail_import__(1, path, locals(), alias, members)
```

例如，导入 maptools 模块的 mapto 成员：

```python
import 'maptools' (mapto)
```

```python
__ail_import__(1, 'maptools', locals(), 'maptools', ['mapto'])
```

导入 printf 模块，并命名为 _printf：

```python
import _printf 'printf'
```

```python
__ail_import__(1, 'printf', locals(), '_printf', [])
```

### load 语句

```python
load path
```

```python
__ail_import__(0, path, locals())
```

load 语句的转换比较简单，这里就不提供例子了。



需要主要的是，AIL 将 `locals()` 作为 namespace 参数，意味着 import 语句影响的名称空间仅为 `local` 。



## struct 定义

struct 是 AIL 相比 Python 特有的一个结构，其被转换成对 `__ail_make_struct__` 函数的调用。

下面给出 `__ail_make_struct__` 的函数签名：

```python
def make_struct(name: str, members: List[str], protected: List[str]) -> _AILStruct:
    ...
```

接下来通过几个例子来了解其中的等效关系。

#### 例1

```go
struct Person {
    name: String
}
```

```python
S = __ail_make_struct__('S', ['name'], [])
```

#### 例2

```go
struct Cat {
    protected type: String
    name: String
}
```

```python
Cat = __ail_make_struct__('Cat', ['type', 'name'], ['type'])
```

