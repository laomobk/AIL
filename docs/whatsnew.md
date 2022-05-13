# AIL 2.3 Diona

AIL 2.3 版本于 2022 年 3 月 20 日开始开发。以下是目前为止 AIL 2.3 版本的主要更新、修复和变更的内容。

## == 更新内容 ==

### 一、yield 语句

yield 语句被用于函数体中，用于声明该函数为 **生成器** ，同时具有与协程传递数据的作用。例如，下面的 `gen_random` 函数将会在输出 6 个范围为 [1, 100] 的随机数后抛出 `StopIteration` 异常：

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

yield from 语句用于在函数中进行委托生成，直到委托生成器结束，函数才会继续向下执行。例如下面的程序，只有依次输出完 `2, 1, 3, 5, 6, 3` 过后，才会打印出 `Generation finished!`。

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
import! os;  // 导入单个 Python 模块
improt! a, b, c;  // 导入多个 Python 模块

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

更多有关 namespace 的内容可以查看 [namespace 说明文档](./reference/namespace.md)

### 五、ShadowAssign 语句

在 AIL 2.3 版本中，可以使用 shadow assign 语句来进行可以跨域搜寻的定义操作。当使用 shadow assign 语句定义一个变量时，若右部的表达式出现了对该变量名的访问，则会对这个变量进行跨域搜寻，搜寻域由 global 到 local，也就意味着，当 local 和 global 中同时出现该变量时，会优先使用处于 global 域的变量。例如：

```go
a = 1;

func f() {
    a = 2;
    a := a + 1;
    print a;  // output: 2
}
```

相比 global 关键字，使用 shadow-assign 可以在使用 global 变量的基础上，对 global 值进行保护：

```go
// foo.ail

a = 1  // outside a

func f() {
    a := a + 1;
    print a;  // inside a
    a = 2;
}

print a;
f();
print a;
```

```shell
$ ail foo.ail
1
2
1
```

一般情况下，该语句可以用于在 namespace 中得到一个来自 global 域的同名变量的拷贝：

```C#
// bar.ail

a = 10;

namespace N {
    a := a;
}

a = 20;

print a;
print N.a;
```

```shell
$ ail bar.ail
20
10
```

更多有关 shadow assign 的内容可以查看[shadow assign 说明文档](./reference/shadow-assign.md)


### 六、带类型注解的赋值语句

在 AIL 2.3 版本中，用户可以对赋值操作加上类型注解：

```
x: int = 10;
```

亦或是单纯地*声明*某个变量：

```
y: int;
```

在上面的例子中，`y` 是有意义的，在一些情况下，`y` 会被 Python 运行时存储到 `__annotations__` 中：

```python
>> class C { y: int; }
>> C.__annotations__
{'y': <class 'int'>}
>>
```

可以使用这种特性去完成一些操作，如可以使用 Python 的 dataclass 装饰器：
```python
from dataclasses import dataclass;

@dataclass;
class Student {
    name: str;
    class_: str;
    score: int;
    rank: int;
}

std = Student('Klee', '1910', 750, 1);
print std;
```
```
Student(name='Klee', class_='1910', score=750, rank=1)
```


## == 修复内容 ==

*暂无*


## == 优化内容 ==

### 一、模块对象的 \_\_name\_\_ 属性增加了模块名称

在先前的 AIL 版本中，若试图访问模块对象中不存在的成员时，会抛出这样的异常：

```python
>> import 'maptools'
>> maptools.x
Traceback (most recent call last):
  File "<shell>", line 1, in <module>
AttributeError: 'AILModule' object has no attribute 'x'
```

开发者并不能通过该错误信息得到具体是对哪个模块进行了非法成员访问。

而在 AIL 2.3 版本中，若非法访问模块对象的成员，则会得到下面的信息：

```python
>> import 'maptools'
>> maptools.x
Traceback (most recent call last):
  File "<shell>", line 1, in <module>
AttributeError: 'AIL Module [maptools]' object has no attribute 'x'
```

这样开发者就能清楚地知道是哪个模块对象了。


## == 变更内容 ==

### 一、模块搜寻顺序调整
自 AIL 2.3 版本开始，AIL 的模块加载顺序调整为：

0. 当前模块的目录 (在 AIL Shell 模式下无此搜寻位置)
1. 当前工作目录，在 AIL Shell 模式下为 `.`
2. AIL 原生模块 ($(AIL\_ROOT)/module/)
3. AIL 标准库 ($(AIL\_ROOT)/lib/)

### 二、内置函数变更

- 【名称变更】：`eval` -> `evaluate`


***最后，希望大家玩的愉快！***

