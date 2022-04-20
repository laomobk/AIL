# namespace 语句

当需要将一系列成员与某作用域独立开来时，可以使用 `namespace` 语句。

## 名称空间

名称空间是用来存放某些成员的数据结构，在外部可以通过名词空间对象来引用名称空间内部的成员。

例如， 我们定义了下面几个波形发生器：

```C#

class WaveGenerator { ... }
class SquareWaveGenerator extends WaveGenerator { ... }
class SawtoothWaveGenerator extends WaveGenerator { ... }

```

当实现的波形发生器越来越多，除了将它们都存放到一个独立的文件中，还可以选择把它们放到名称空间中：

```C#

namespace WaveGenerators {
    class WaveGenerator { ... }
    class SquareWaveGenerator extends WaveGenerator { ... }
    class SawtoothWaveGenerator extends WaveGenerator { ... }
}

```

这个时候，这些波形发生器就和其他作用域独立开来了。我们想要使用这些发生器，就得通过 `WaveGenerator` 名称空间来引用：

```
saw_gen = WaveGenerators.SawtoothWaveGenerator();
```

## 名称空间的域

名称空间中的域是与外界独立的，在名称空间内部的定义语句对外界不产生影响：
```C#

x = 1;

namespace N {
    x = 2;
}

print x;  // 1

x = 3;

print N.x;  // 2
```

## 使用名称空间导出模块成员

从 AIL 2.3 开始，用户可以定义一个名称为 `__export__` 的名称空间来存放 *导出成员* ，例如有模块 `foo` ：

```swift
func _get_code(code): int {
    return ~(code << 1);
}


code = _get_code(727);
```

通常，我们想定义一个不想被用户使用的成员时，会在名称前添加单下划线，告诉用户这是不应该使用的。但通过名称空间导出，就不会为可见性而烦恼：
```C#
func get_code(code): int {
    return ~(code << 1);
}


namespace __export__ {
    code = get_code(727);
}
```

这样下来，对于 foo 模块，用户在使用时，`get_code` 就是不可见的了：

```python
AIL 2.3 Diona alpha 1 [728] (2.3/d7ba182) (Python 3.8.0 (default, Dec  5 2019, 10:53:43)
[Clang 8.0.7 (https://android.googlesource.com/toolchain/clang b55f2d4ebfd35bf6)
Type 'help(...)', '$help', 'copyright()', 'python_copyright()' to get more information, 'exit()' to exit.

>> import 'foo';
>> foo.code;
foo.code
>> foo.code
-1455
>> foo.get_code
Traceback (most recent call last):
  File "<shell>", line 1, in <module>
AttributeError: 'AILModule' object has no attribute 'get_code'
```

## 注意事项

1. 一般情况下，名称空间是用于存放定义语句的，在名称空间中使用其他类型的语句是*不被推荐*的。
