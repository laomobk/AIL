# AIL 介绍

AIL 是一门运行在 Python 虚拟机上的编程语言，它支持决大多数 Python 的特性，同时，它也有自己的特性。

AIL 具有类似 JavaScript 的语法。相比 Python 来说，语法上少了几分的美观；但是 AIL 对自由格式代码有较好的支持。某些程度上，AIL 就是具有类似 JavaScript 语法的 Python。

```go
func fib(n) {
    if n == 1 or n == 2 {
        return 1;
    } else {
        return fib(n - 2) + fib(n - 1);
    }
}
```

