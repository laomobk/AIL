
# AIL 语句

> AIL 2.1 alpha 1
> 2021.7.26

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

三段式 for 语句头部分别为 ***init; test; update*** 。for 语句循环体开始被执行前，执行 init 部分的内容，接着 test 部分会被执行，并且

#### 单条件 for 语句
```python
for expression { statements }
```

### foreach 语句
```python
foreach expression in expression { statements }
```

### do 语句
```swift
do { statements } loop until expression;
```

### continue 语句

```python
continue;
```

### break 语句

```python
break;
```

### return 语句

```python
return [expression];
```

### throw 语句

```python
throw [expression];
```

### assert 语句

```python
assert expression;
```


## 定义语句与赋值语句

### 赋值语句
```python
expression = expression;
```

### 函数定义语句
```swift
func [ ( NAME ) ] NAME (arg [, arg]* [, *arg] [, **arg]) { statements }
```

### 类定义语句
```swift
class NAME [: expression] [extends expression [, expression]] { statements }
```

### 名称空间定义语句
```swift
namespace NAME { statements }
```

### 结构体定义语句
```swift
struct NAME {
    [[protected NAME;] | [NAME;]]*
}
```

## 加载语句和导入语句

### import 语句
```python
import [NAME] STRING [(NAME [, NAME]*)];
```

### load 语句
```python
load STRING;
```

## Python 嵌入代码语句
```
#py_statement
```

