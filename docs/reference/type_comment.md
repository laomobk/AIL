# Type Comment 语法

AIL 支持给函数的形式参数、返回值，赋值语句的左值进行类型注释。

类型注释语法如下：

```
(...) ':' Cell
```



## 函数定义时使用类型注解

可以给函数的形式参数列表进行类型注解：

```swift
func f(a: int, b: str) {
    // ...
}
```

同时也可以对函数的返回值进行类型注解：

```swift
func f(a: int): int {
    // ...
}
```



## 赋值语句使用类型注解

可以对赋值语句左值使用类型注解：

```python
a: int = 726;
```

注意，不能够在 assign 元组中使用类型注解：

```python
>> a, b: int = 1, 2;
File "<shell>", line 1
    a, b: int = 1, 2;
SyntaxError: only single target (not tuple) can be annotated
```



## 其他情况

不能够在除了上述情况下使用类型注解，否则 AIL 将会抛出语法错误。