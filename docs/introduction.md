
# AIL 介绍

欢迎使用 AIL ！

## AIL 是什么

AIL 是运行于 Python 虚拟机之上的编程语言。支持绝大部分来自 Python 的特性，同时在此基础上加入了如*匿名函数*、*名称空间*等特性。

## 友好的语法

AIL 采用了自由格式的语法，使用 *大括号* 来组织代码，并可使用分号作为语句的结束：

```python
func fib(n) {
    if n == 1 or n == 2 {
        return 1;
    } else {
        return fib(n - 2) + fib(n - 1);
    }
}

```

## 优秀的互操作性

你可以在 AIL 中使用任何的 Python 模块，包括 requests, flask, numpy，同时，AIL 还兼容大部分来自 Python 的语法，如关键字参数，解包操作等。

```go
import! numpy as np;  /* 使用 import! 导入 python 模块 */
import! matplotlib.pyplot as plt;

N = 50;
xy_data = np.random.rand(N), np.random.rand(N);
colors = np.random.rand(N);
area = (30 * np.random.rand(N)) ** 2;

plt.scatter(*xy_data, s=area, c=colors, alpha=0.5);

plt.show();
```

## 极低的依赖

***「有 Python 的地方就能运行 AIL！」***

AIL 的实现几乎没有引用其他第三方库（除了 astunparse，但也是非必须的）。这意味着您可以直接在一个有完整的 Python3.7 （或以上的版本）运行时中直接运行 AIL 。

AIL 主要用到了以下来自标准库的模块：
- os
- os.path
- sys
- traceback
- importlib
- typing
- inspect
- time
- types

## 多版本支持

AIL 支持最低到 Python 3.7 版本。在 Python 3.6 版本中亦可支持大部分的 AIL 特性。目前 AIL 已经经过在 Python 3.10 的运行测试。

