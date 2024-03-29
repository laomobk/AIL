# match 表达式

```
version: 20220501
AIL version: 2.3a2
```

本篇文章将简单介绍 match 语句并讲述 AIL 中 match 表达式的工作原理，以便开发者更好地使用 match 表达式。

## 介绍

match 表达式可以方便地对给定的对象进行模式匹配操作。通常，match 表达式一般具有如下形式：

```swift
result = match p {
   Point! {x: 10, y: 100}: -1,
   Point! {x: 10, y: 50}: 0,
   Point! {x: 10, y: 0}: 1,
}
```

## match 语句的组成
match 语句由 target, case 两部分组成，下面来依次介绍各个部分：

### target 部分

target 部分是用于进行模式匹配的对象，可以是任何对象。target 部分同样支持填写**赋值表达式**：
*AIL 目前为止并未真正支持表达式形式的赋值语句(即可以返回所赋的值的表达式)*

```
message = match stu_code = get_status_code(response) {
    200: '%s ok' % stu_code,
    404: '%s page not found' % stu_code,
}
```

上面的代码会被转换为如下的等效代码 (代码经过格式化)：
```python
stu_code = get_status_code(response)
message = (('%s ok' % stu_code) \
    if ail::match(stu_code, (200,), True) else (('%s page not found' % stu_code) \
        if ail::match(stu_code, (404,), True) else \
            py::raise(py::UnhandledMatchError('unhandled match value'))))
```

通过阅读转换后的代码不难看出，当 target 部分出现赋值操作时，会在匹配部分的先前一行进行赋值操作，**这一操作将对本地作用域造成影响。**

### case 部分

case 是 match 进行匹配的执行单元。case 分为：
 - pattern case
 - when case
 - else case

每个 case 都对应着 value。

case 在 match 语句中按顺序排列，从上到下执行，直到匹配成功。

#### pattern case

pattern case 代表执行模式匹配操作，其语法如下：

```
expression [',' expression]*
```

每一个 pattern case 都会被转换为下面的函数调用：

```python
# ail/core/functions.py

def ail_match(target, patterns: list, only_constant: bool) -> bool:
    if only_constant:
        return target in patterns  # mark 1
    for pattern in patterns:
        if hasattr(pattern, '__match__'):
            if pattern.__match__(target):
                return True
        else:
            return target == pattern

    return False
```

`ail_match` 会调用 pattern 的 `__match__` 进行匹配，若不存在此方法，则会使用 `==` 运算符进行比较，而如果 pattern 为字面量，则直接使用原生的比较操作（见 mark 1 部分）

使用 `,` 可以分隔多个 pattern，这多个 pattern 会按顺序匹配。

#### when case

when case 将直接检测给予的表达式的真假：

```
'when' expression
```

```swift
match num {
    when num == 2: 100
}
```

上面的 AIL 代码会被转换为下面的 python 代码：
```python
<match_value_33828402378-1> = num
(100 if (num == 2) else py::raise(py::UnhandledMatchError('unhandled match value')))
```

不难发现，when 后面的内容会被直接作为 if 表达式的 condition 部分。

#### else case

else case 通常情况下是放到 case 列表的最后一位，当前面所有的 case 都未被执行时，else case 就会被执行（前提是给出）。

```python
print match err {
    TypeError: 'wrong type!',
    NameError: 'name not found!',
    else: 'an error occured: %s' % err,
}
```

else case 在模式匹配中相当于匹配任何对象。

## 异常的抛出

当没有能与之相匹配的 match case 时候，match 表达式会抛出 `UnhandledMatchError`。因此在大多数情况下，在 match 中加入 else case 是聪明的选择。

```python
>> match 0 { 1: 0,}
Traceback (most recent call last):
    File "<shell>", line 1, in <module>
ail.core.exceptions.UnhandledMatchError: unhandled match value
```

## 自定义 pattern 匹配
通常情况下，pattern 可以是任意对象如字符串、数字、某个对象，pattern 的匹配也使用普通的 `==` 比较符。当需要自定义匹配的过程时，需要对象提供 `__match__` 方法，若检测到 pattern 拥有此方法，则优先调用该方法，并对该方法的返回值进行布尔判断。

`__match__` 方法具有如下的形式：
```swift
func __match__(self, target: object): bool { ... }
```

例如 AIL 提供的 `ObjectPattern` 类型就提供了如下的 `__match__` 方法：
```python
# ail/core/objects.py

class ObjectPattern:
    ...

    def __match__(self, target) -> bool:
        if not isinstance(target, self.__type):
            return False

        for k, v in self.__kv_dict.items():
            if not hasattr(target, k) or getattr(target, k) != v:
                return False

        return True

    ...
```

