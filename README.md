# AIL 2.2 alpha 0

![AIL 2.2 Klee 版本更新](./docs/whatsnew.md)

![AIL badge](https://img.shields.io/badge/AIL-Programming%20Language-blue)
![python badge](https://img.shields.io/badge/python-3.6%2B-blue)
![version badge](https://img.shields.io/badge/version-2.1%20alpha-success)
![license badge](https://img.shields.io/badge/license-GPL-blue)

AIL 是一门运行在 Python 虚拟机上的面向对象的编程语言。支持 Python 的诸多特性的同时，也拥有 AIL 自身的特性。

***注意：从 2.1 版本开始，AIL 自带的虚拟机和编译器已经被禁用，默认启用 Python 兼容模式***

## 环境需求

**具有完整标准库的 Python3.6+, 最好是 3.7 ~ 3.8 版本**

AIL 需要运行在具有完整标准库的 Python 环境上，版本最低不低于3.5，3.5 ~ 3.6 之间的 Python 版本不确保有正常的 AIL 使用体验。若要取得最好的 AIL 体验，请使用 3.7 ~ 3.8 版本的 Python, 3.9+ 的 Python 版本运行 AIL 并不稳定。

推荐使用 **cpython** 解释器，其他 Python 解释器并未进行过测试。

## Hello World

#### Hello World with one statement
```python
print 'Hello World';
```
..or..
```python
console.writeln('Hello World!');
```

#### Hello World in lambda
```python
(() -> console.writeln('Hello World'))();
```

#### Hello World in function
```swift
func helloWorld() {
    print "Hello World!";
}

helloWorld();
```

#### Hello World in anonymous function
```swift
(func () {
    print "Hello World!";
})();
```

#### Hello World in class
```swift
class Hello {
    func helloWorld(self) {
        print "Hello World!";
    }
}

Hello().helloWorld();
```

#### 斐波那契数列

```swift
func fib(n) {
    if n == 1 or n == 2 {
        return 1;
    } elif n >= 2 {
        return fib(n - 2) + fib(n - 1);
    }
}
```

## 主要语言特性

*以下例子均已在 AIL 2.1 版本下通过编译*

### 更多的 for 语句

```swift
for i = 0, j = len(x); i < len(x); i += 1, j -= 1 {
    // ...
}

for {
    // forever...
}

foreach i in range(100) {
    // ...
}
```

### 强大的 match 表达式

```swift
name = match lang_name {
    'Python': 'py',
    'Java': 'java',
    'AIL': 'ail',
}

(match point {
    Point! { x: 5, y: 6 }: () -> {
        // handle it...
    },
    else: () -> {
        // handle it...
    }
})();
```

## VIM 语法高亮支持

AIL 为 vim 专门编写了其语法高亮文件，写代码的时候妈妈再也不会担心敲错关键字了！

提供了如下高亮支持：

- 关键字
- 字符串、数字
- 基本类型注解
- AIL 内置函数、常量 （并未高亮 Python 的内置函数与常量）

![vim highlight](https://gitee.com/LaomoBK/ail/raw/2.1/misc/vim_highlight.jpg)

#### 配置

1. 将 **plugin/vim/syntax/ail.vim** 与 **plugin/vim/ftdetect/ail.vim** 分别复制到 **{VIM_HOME}/syntax/** 和 **{VIM_HOME}/ftdetect/**

2. 重新启动 vim 即可

## 安装 AIL

运行 AIL 事先准备好的 **setup.py** 可以非常快速地在您的电脑上配置好 AIL。

```sh
python setup.py install
```

在终端中输入:
```
ail
```

或者

```
python3 -m ail
```

***Windows下应确保 {PYTHON_HOME}/Script/ 已添加到 PATH 中***
***Linux/Mac OS 下应确保当前用户的 bin 目录已添加到 PATH 中***

若进入 AIL 的交互环境，则安装成功。

## 文档

AIL 的文档仍然在完善中。具体的进度可以在 `/docs/` 中查看。

## AIL 语句
文档 [AIL语句](./docs/reference/statements.md) 简要地描述了 AIL 的语句

## AIL 代码转换细节

想要了解 AIL 代码是如何转换成 Python 语法树的，可以查看：

 [ail_in_python](./docs/developer/ail_in_python.md)

## tree.txt

这是最早期 AIL 语法分析器生成的语法树

*对应的程序**应该**可以在早期 commit 中找到*
