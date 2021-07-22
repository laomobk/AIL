# 名字空间 (namespace)

> Date: 2021/7/22
> 
> Latest version: 2.1 alpha 1

名称空间是 AIL alpha 1 加入的一个特性，其作用是为了能够使得成员之间的名称空间独立开来。

其语法如下：

```python
namespace <namespce_name> {
    ...
}
```

若需要访问名称空间里面的成员，需要在成员名前面添加限定：

```
<namespace_name>.<member>
```

***e.g.***

```python
namespace MyNamespace {
    a = 1;
    b = 2;
}

print MyNamespace.a
```

在内部访问名称空间的成员则不需要添加限定：

```swift
namespace MyNamespace {
    a = 1;
    func f() {
        return a + 1;
    }
}

print MyNamespace.f()
```

