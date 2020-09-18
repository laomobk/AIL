builtins -- 内建模块
~~~~~~~~~~~~~~~~~~~~

*(构建中...)*

builtins是AIL运行时启动后自动加载的 **"模块"** ，提供了一些基本的操作。
**注意: builtins模块实现abuiltins.py并不被设计成为AIL的扩展模块**

*builtins实现可以查看源码: ail/core/abuiltins.py*

builtins.abs(x: number) -> number
#################################

提供了取绝对值操作。

::

    >> abs(-726)
    < 726 >
    >> abs(726)
    < 726 >


builtins.ng(x: number) -> number
################################

提供了将正数取反的操作。

*最早的AIL并不支持表示负数，需要使用这个函数取负数*

::

    >> ng(726)
    < 726 >
    >> ng(-726)
    < -726 >


builtins.int_input(prompt: string) -> integer
#############################################

提供了整数输入操作，若接受了一个非数字输入，则抛出 :code:`ValueError` 。

::

    >> int_input('What is your score: ')
    What is your score: 150
    < 150 >

    >> int_input('What is your score: ')
    What is your score: A+
    in '<shell>' + 4 :
        ValueError : invalid literal for int() with base 10: 'A+'


builtins.chr(x: integer) -> string
##################################

返回一个Unicode字符，值介于 [0, 0x10FFFF]，若超出该范围，则抛出 :code:`PythonError` 。

::

    >> chr(51)
    '3'
    >> chr(-51)
    in '<shell>' + 4 :
        PythonError : chr() arg not in range(0x110000)


*将在未来版本修改为 UnicodeError*

builtins.ord(x: string) -> integer
##################################

返回 **单字符字符串串** :code:`x` 的 **Unicode Point** 。若x不符合要求，则抛出 :code:`PythonError`
**x 必须是单字符字符串，即len(x) == 1**

::

    >> ord('N')
    < 78 >
    >> ord('NZ')
    in '<shell>' + 4 :
        PythonError : ord() expected a character, but string of length 2 found


