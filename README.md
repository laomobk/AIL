# AIL 1.2 Alpha 2


![AIL badge](https://img.shields.io/badge/AIL-Programming%20Language-blue)
![python badge](https://img.shields.io/badge/python-3.6%2B-blue)
![version badge](https://img.shields.io/badge/version-alpha%201.2-success)
![license badge](https://img.shields.io/badge/license-GPL-blue)

AIL 是一门面向对象的编程语言。具有许多高级易用的数据结构以及语法简洁，功能强大的特点。

## Hello World

#### Hello World with one statement
```
print 'Hello World'
```
..or..
```
console.writeln('Hello World!')
```

#### Hello World in lambda
```
(() -> console.writeln('Hello World'))()
```

#### Hello World in function
```
func helloWorld() {
    print 'Hello World!'
}

helloWorld()
```

#### Hello World in anonymous function
```
(func () {
    print 'Hello World!'
})()
```

#### Hello World in class
```
class Hello {
    func helloWorld(self) {
        print 'Hello World!'
    }
}

Hello().helloWorld()
```

## 构建 / 安装

运行 AIL 事先准备好的 **setup.py** 可以非常快速地在您的电脑上配置好 AIL。

```sh
python setup.py install
```
