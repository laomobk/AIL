
# AIL 语句

> AIL 2.3 alpha 0
> 2022.3.20

AIL 程序由一条条语句构成，下面来按照类别逐一简单地介绍 AIL 的各个语句。

## 输入、输出语句

### input 输入语句
```swift
input expression [, name1, name2, ...];

// e.g.
input 'age: ', age;
```

input 语句用于从 `stdin` 中读取数据。一般情况下，input 语句在等待用户输入时会将当前线程阻塞。input 右边的第一个表达式是 **必须的** ，而后面跟随的名称列表则是可选的。名称列表的长度会影响 input 语句对输入数据的处理方式：

- 若无名称列表，则只是读取输入流。读到的数据将会被抛弃。
- 若名称列表长度为 **1**，则将读取到的输入存储到 name 中，若 name 未被定义，则会在 local 域定义 name.
- 名称列表长度 **大于1**，则将读取到的输入 **以 ***一个空格***  进行分割分别依次存储到名称列表的各个项中**，对未定义名称的处理与单个名称时的处理方式相同。

**注意：input 语句虽然对作用域产生影响，但其属于隐式定义语句，在 namespace 中使用会出现风险**

### print 输出语句
```swift
print expression [, expression]*;
```

print 语句用于向 `stdout` 写入数据。若提供多个表达式，则会以 ***一个空格*** 为分隔符进行输出。

print 语句会调用对象的 `__str__` 方法的返回值进行输出。

## 流程控制语句

### if-elif-else 语句

```swift
if expression { statements } [ elif expression { statements } ]* [ else { statements } ]

// e.g.
if c == 1 {
    // ...
} elif c > 5 {
    // ...
} elif c > 1 {
    // ...
} else {
    // ...
}
```

### while 语句

```python
while expression { statements }
```

while 语句将重复执行循环体直到 `bool(expression) == False` 

### for 语句

#### 三段式 for 语句
```python
for expression [, expression]* ; expression ; expression [, expression] * { statements }
```

三段式 for 语句头部分别为 `for init; test; update {...}` 。init 部分非常特殊，在这个部分，您可以将赋值语句作为表达式使用，多个赋值语句使用逗号（不是分号）隔开：

```python
for i = 0, j = 0; i < j; i += 1 {...}
```

for 语句循环体开始被执行前，执行 init 部分的内容，接着 test 部分会被执行，并且会其进行判断，若首次判断为 **False** ，则不执行循环体，直接到下一条语句。执行完循环体后， update 部分的语句会被执行。重复整个过程，直到 test 部分的值为 **False** 。

#### 单条件 for 语句
```python
for expression { statements }
```

单条件 for 语句的使用方式和 while 语句类似，这里就不多阐述。

### foreach 语句

```c#
foreach NAME [, NAME] in expression { statements }
```

foreach 语句是迭代循环语句。其各部分的职能如下：`foreach target in iterator {...}` 。iterator 部分的值应该是一个可迭代对象，如 `str` 、`list` 。target 部分是一个 ***NameList*** ，用于存储 iterator 每次迭代后返回的值。等效于 while 语句：

```java
try {
    _iter = iter(iterator);
    target = next(_iter);
    while true {
        try {
            /* statements... */
        } finally {
            target = next(_iter);
        }
    }
} catch StopIteration _ { /* do nothing... */ }
```

### do 语句

```swift
do { statements } loop until expression;
```

do 语句属于先执行后判断的循环语句。循环体先会被执行，接着进行判断，若 `bool(expression) == True` ，则结束循环，执行下一条语句，否则再次执行循环体。

### try 语句

```
try { statements } [catch expression NAME { statements }]* [finally { statements }]
```

 try 语句多用于捕获异常并根据异常类型进行处理。try 的 catch, finally 组合规则是：**try 语句的下方分别可以跟一个多个 catch 或一个 finally，若同时拥有一个或多个 catch 和 finally ，则必须将 finally 写在 catch 下方。** 因此，try 语句分为 try - catch [- finally] 型和 try - finally 型。

#### try - catch [ -finally] 型

这类语句通常拥有如下形式，其中 finally 是 **可选** 的：

```java
try {
    /* some code... */
} catch TypeError e {
    /* handle type error */
} catch ValueError e {
    /* handle value error */
} finally {
    /* some code... */
}
```

#### try - finally 型

这类语句通常拥有如下形式：

```java
try {
    /* some code... */
} finally {
    /* some code ... */
}
```

#### catch 匹配规则

当 try 语句块中有异常抛出时，若该 try 语句有 catch ，则会按从上往下的顺序匹配 **异常类型** 。当异常类型符合 `issubclass(cur_exc_type, given_exc_type)` 则进入该 catch 块，并且将异常对象赋值到 catch 给定的名称。若找不到相应的 catch ，则运行时会重新回到 panic 状态（重新抛出异常）。***catch 的赋值属于隐式定义，会对 local 名称空间造成影响，当 catch 名称与 local 内的某个变量名称相同，该变量可能会被覆盖并且被删除。*** 

### continue 语句

```python
continue;
```

continue 语句只能用在循环语句中。用于跳过循环体内，continue 以下的语句，开始新的一轮循环。

### break 语句

```python
break;
```

break 语句只能用在循环语句中。用于跳出循环。

### return 语句

```python
return [expression];
```

return 语句只能用在函数体内。return 语句用于向调用者返回值。return 语句的 `expression` 是可选的，当不提供返回值，则默认返回 `null` 。

### yield 语句

```python
yield [from] [expression];
```

yield 语句被用于**生成器**函数中，而且只能用于函数体中。

#### yield 赋值

**当且仅当** yield 作为赋值语句的右边部分的时候，yield 可以作为表达式使用：

```python
func f() {
    x = yield 10;
}
```

### throw 语句

```python
throw [expression];
```

throw 语句用于向当前运行时抛出异常。当 throw 置于 catch 中时，`expression` 时可选的，此时的 throw 语句会重新抛出被当前 catch 捕获的异常。

### assert 语句

```python
assert expression;
```

assert 语句用于进行断言。当 `bool(expression) == False` 时，该语句就会向运行时抛出 `AssertionError` 。

### with 语句

with 语句可以方便地使用上下文管理器，让上下文管理器随着代码一起执行。

```
with_stmt := 'with' with_item [';' with_item] block
with_item := [assign_tuple '='] expression
```

当有多个 with_item 的时候，语义上相当于多个 with 语句嵌套:

```python
with a = A(); b = B() {
    // ...
}
// equals...
with a = A() {
    with b = B() {
        // ...
    }
}
```

## 定义语句与赋值语句

### 赋值语句
```python
assign_tuple = expression;
```

赋值语句属于显式定义语句。

赋值语句不能作为表达式使用。

assign_tuple 部分是特殊的表达式，在一定意义上成为左值表达式。assign 部分可以是下标索引表达式，可以是成员访问表达式，也可以是特殊的 assign 元祖。

assign 元祖中的项目必须是左值表达式，当赋值表达式右边为**可解包对象**的时候，解包结果会被分别赋值给 assign 元祖：

```python
a, b, c = c, b, a;
```

### 函数定义语句

```swift
func [ ( NAME ) ] NAME (param [, param]* [, *param] [, **param]) { statements }
```

函数定义属于显式定义语句。具体结构名称如下：

```swift
func [bind] name param_list { statements }
```

bind 是可选的，若定义 bind, 则代表该函数是相应结构体的 **绑定函数** ，需要注意的是，绑定函数部分不能是表达式，而是一个 name 。

### 类定义语句

```swift
class NAME [: expression] [extends expression [, expression]] { statements }
```

类定义语句属于显式定义语句。具体结构名称如下：

```python
class name [:meta_class] [extends super_class...]
```

若不指定 meta_class，则默认是 `type` ，若不指定 super_class, 则默认是 `object` 。

### 结构体定义语句

```swift
struct NAME {
    [[protected NAME;] | [NAME;]]*
}
```

结构体定义语句属于显式定义语句。在结构体中可以定义 *保护成员* ，其中，保护成员不可在绑定函数外被修改。

## 加载语句和导入语句

### import 语句
```python
import [NAME] STRING [(NAME [, NAME]*)];
```

import 语句各结构名称如下：

```python
import [alias] module_path [(mumber...)];
```

import 语句将会将加载模块导入到 **local** 中。若指定 alias, 则将导入模块的名称改为指定的别名。

若指定 member, 则会导入模块中响应的成员。alias 和 member 被同时指定时，将会有语法错误。

*e.g.*

```python
import 'a' (a, b);
```

```python
import x 'a';
```

### load 语句

```ruby
load STRING;
```

load 语句用于将模块的 **所有** 导出成员导入到 **local** 中。


## Python 嵌入代码语句

```
#py_statement
```

Python 嵌入代码将会被直接编译成相应的 Python 语法树。



> 2022.3.20 Laomo.

