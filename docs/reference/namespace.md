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

print MyNamespace.a;
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



## 注意事项

namespace 的底层实现原理是将 namespace 使用函数包裹，使用闭包的特性以达到不加限定符而进行名称空间内成员访问的的效果。

其中，名称空间内成员的定义应该 **显式书写** 。实际上，在一般情况下， namespace 的无限定符名称索引都能正常工作。

下面列举一些具有风险的操作。

```python
namespace A {
    #locals().update({'a': 1})
    func f() {
        return a;
    }
}

print A.a;
print A.f();

```

***下面我们来运行这个程序：***

```shell
$ ail .\tests\test.ail
1
Traceback (most recent call last):
  File ".\tests\test.ail", line 9, in <module>
    print A.f();
  File ".\tests\test.ail", line 4, in f
    return a;
NameError: name 'a' is not defined
```

我们隐式地注入 a 成员到名字空间 A 中，使得第一条 print 得以正常工作，但调用 `A.f` 后，程序出现 `NameError` 。

我们可以通过任何 **显式定义语句** 来填充名字空间。严格来讲，Python 编译器会检查 AST 中 `Name` 类型节点的 `ctx` 属性，如果是 `Store` 上下文，则属于显式定义。一般来说，正常的定义语句，类定义语句，函数定义语句，都属于显式定义语句，当然，for 语句也是显式定义语句：

```python
namespace A {
    foreach i in range(100) {}
}

print A.i;
```

程序依然能够正常输出，因为变量 `i` 的上下文为 `Store` 。

