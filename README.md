# AIL 2.1 alpha 0


![AIL badge](https://img.shields.io/badge/AIL-Programming%20Language-blue)
![python badge](https://img.shields.io/badge/python-3.6%2B-blue)
![version badge](https://img.shields.io/badge/version-alpha%202.1-success)
![license badge](https://img.shields.io/badge/license-GPL-blue)

AIL 是一门运行在 Python 虚拟机上的面向对象的编程语言。

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

## 安装 AIL

运行 AIL 事先准备好的 **setup.py** 可以非常快速地在您的电脑上配置好 AIL。

```sh
python setup.py install
```

在终端中输入:
```
ail
```

***Windows下应确保 {PYTHON_HOME}/Script/ 已添加到 PATH 中***
***Linux/Mac OS 下应确保当前用户的 bin 目录已添加到 PATH 中***

若进入 AIL 的交互环境，则安装成功。
