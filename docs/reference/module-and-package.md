# AIL 的包、模块机制

> version: 
>
>    2021/7/13
>
>    2022/5/1
>
> Latest version: 2.3 alpha 2

## AIL 模块

模块是最基本的代码单位，AIL 程序由一个个模块组成，每个模块可以通过 `import` 语句来相互连结。一个 AIL 文件就是一个模块。

```swift
// a.ail

info = 20200727
```

```swift
// b.ail

import './a'

print a.info
```

这是最基本的模块间连接方式：模块 b 导入了 **同级目录** 下的模块 a，并且访问内部成员。值得注意的是，b 模块的 import 语句的对象是 `./a` ，这种写法告诉 AIL 应该使用相对导入。类似地，如果 a 模块在同目录下的一个子目录内，则应该这样写： `import './foo/a'` 。目录分隔斜杠使用 **unix** 风格。

## AIL 包

包是又一个 AIL 组织代码的方式，包由一个个模块组成，一般来说，包是一个带有 `_package.ail` 的文件夹。当导入包时，实际上就是导入 `_package.ail` 。

```swift
// mypkg/_package.ail


print '_package.ail loading...'
date = 20200726
```

```python
>> import 'mypkg/'
_package.ail loading...
>>
```

注意，在导入包时，需要在包名后加 `/` 。
