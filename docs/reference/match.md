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
   Point ! {x: 10, y: 100}: -1,
   Point ! {x: 10, y: 50}: 0,
   Point ! {x: 10, y: 0}: 1,
}
```

## match 语句的组成
match 语句由 target, pattern, value 三部分组成，下面来依次介绍各个部分：

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
