
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

### print 输出语句
```swift
print expression [, expression]*;
```


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

### for 语句

#### 三段式 for 语句
```python
for expression [, expression]* ; expression ; expression [, expression] * { statements }
```

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

