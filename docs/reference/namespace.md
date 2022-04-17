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

## 注意事项

1. 一般情况下，名称空间是用于存放定义语句的，在名称空间中使用其他类型的语句是*不被推荐*的。