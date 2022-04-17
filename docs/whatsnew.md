# AIL 2.3 Diona

AIL 2.3 版版本于 2022 年 3 月 20 日开始开发。以下是目前为止 AIL 2.3 版本的主要更新、修复和变更的内容。

## == 更新内容 ==

### 一、yield 语句

yield 语句被用于函数体中，用于声明该函数为 **生成器** ，同时具有与协程传递数据的作用。例如，下面的代码将会在输出 6 个范围为 [1, 100] 的随机数后抛出 `StopIteration` 异常：

```python
from random import randint;


func gen_random(n) {
    foreach _ in range(n) {
        sig = yield randint(1, 100);
        if sig {
            break;
        }
    }
}


g = gen_random(10);
foreach i, x in enumerate(g) {
    print x;
    if i > 5 {
        g.send(1);
    }
}
```

#### yield form 语句

yield from 语句用于在函数中进行委托生成，直到委托生成器结束，函数才会继续向下执行。例如下面的程序，只有一次输出完 `2, 1, 3, 5, 6, 3` 过后，才会打印出 `Generation finished!`。

```python
func f(*args) {
    foreach arg in args {
        yield from arg;
    }
    print 'Generation finished!';
}


foreach x in f((2, 1, 3), [5, 6, 3]) {
    print x;
}
```


### 二、Python import 语句

AIL 2.3 版本加入了来自 Python 的 import 与 import from 语句，用于导入 Python 模块。

```python
import os;  // 导入单个 Python 模块
improt a, b, c;  // 导入多个 Python 模块

from os import path; // 导入 Python 模块的单个成员
from typing import List, Tuple;  // 导入 Python 模块的多个成员
```


### 三、\_\_file\_\_ 变量

在 AIL 2.3 版本中，可以通过 `__file__` 变量得到当前 AIL 程序的路径，这个路径是**用户使用 AIL 执行此程序时给出的文件路径**。

```python
// ~/foo.ail

print __file__; 
```
下面是该程序在 shell 中的执行情况：
```shell
pi@raspberrypi:~ $ ail ~/foo.ail
~/foo.ail
pi@raspberrypi:~ $ cd ~/ail/ail/core/
pi@raspberrypi:~/ail/ail/core $ ail ../../../foo.ail 
../../../foo.ail
pi@raspberrypi:~/ail/ail/core $
```


### 四、名称空间

在 AIL 2.3 版本中，用户可以使用 `namespace` 语句定义名称空间：
```python
namespace Apple {
    os = 'MacOS';
    computer = 'Mac';
}

namespace Microsoft {
    os = 'Windows';
    computer = 'PC';
}
```


## == 修复内容 ==

*暂无*

## == 变更内容 ==

### 一、模块搜寻顺序调整
自 AIL 2.3 版本开始，AIL 的模块加载顺序调整为：

0. 当前模块的目录 (在 AIL Shell 模式下无此搜寻位置)
1. 当前工作目录，在 AIL Shell 模式下为 `.`
2. AIL 原生模块 ($(AIL_ROOT)/module/)
3. AIL 标准库 ($(AIL_ROOT)/lib/)
