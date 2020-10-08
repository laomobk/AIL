builtins -- 内建模块
~~~~~~~~~~~~~~~~~~~~

*(构建中...)*

builtins是AIL运行时启动后自动加载的 **"模块"** ，提供了一些基本的操作。

**注意: builtins模块实现abuiltins.py并不被设计成为AIL的扩展模块**

*builtins实现可以查看源码: ail/core/abuiltins.py*


type string
###########

表示基本字符串

::

    >> 'nezha'
    'nezha'
    >> "Nezha"
    'Nezha'



type integer
############

表示整数。

::

    >> 3
    < 3 >
    >> -15
    < -15 >


type float
##########

表示64位浮点数。

::

    >> 10 / 3
    < 3.3333333333333335 >
    >> 1.0
    < 1.0 >
    >> 3 / 1.0  // convert to float
    < 3.0>


type array
##########

表示定长数组类型。其容纳的类型是任意的。

::

    >> {1, 2.0, '3', fnum(4), _get_ccom}
    {
        < 1 >, 
        < 2.0 >, 
        '3', 
        < 4 >,
        <AIL Python function wrapper 'get_cc_object' at 0x7d97609c40>
    }


*（由于输出过长，上面REPL部分输出经过调整，实际输出并没有换行）*


type CCOM_T
###########

由 :code:`_get_ccom()` 函数返回其对象。不能被实例化。


type iobuffer_t
###############

文件IO缓冲类型，由 :code:`open(...)` 返回其对象。用于对文件进行操作。不能被初始化。


type longish
############

具有长度的对象，即可以使用 :code:`len(...)` 的对象。
一般情况下，longish对象包括:

* string
* array


type fast_number
################

fast_number 类型是AIL中的特殊类型。由 :code:`fnum(...)` 返回其对象。不能被初始化。引入的目的是为了使得AIL运行得更快。
fast_number 之间的运算相比普通的数字类型运算，效率会高很多。

::
    
    >> fnum(1)
    < 1 >
    >> a = fnum(3)
    >> b = fnum(1)
    >> a + b
    < 35 >


type struct_type
################

**struct类型** 类型。struct_type 用于生成struct_object, 即 **object** 。

::

    >> struct Person is
    ..      name
    .. end
    >> Person  // struct_type
    <struct 'Person' at 0x7d97631df0>


type object
###########

**object** 指struct_type经过实例化后，得到的 **struct_object** 。

::
    
    >> struct Person is
    ..      name
    .. end
    >> Person
    <struct 'Person' at 0x7d97631df0>

    >> new(Person)
    >> new(Person)
    <struct 'Person' object at 0x7d973c0340> -> {
        name : null
    }


type any
########

表示任意类型。


type null
#########

null 类型。


type bool
#########

表示布尔类型。


union number
############

表示 **float类型** 或者 **integer类型** 。


var null: null
##############

null 表示“空”，在AIL中，null是一个变量名，一般情况下，null可以被赋值 *（但不建议这么做）* 。

::
    
    >> if null then
    ..     print 'Should not be printed'
    .. end
    >>


var true: bool
##############

表示“真”。


var false: bool
###############

表示“假”。


var __version__: string
#######################

AIL版本字符串。


var __main_version__: integer
#############################

AIL主版本号。


var console: console
####################

用于操作控制台的对象


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

返回 **单字符字符串** :code:`x` 的 **Unicode Point** 。若x不符合要求，则抛出 :code:`PythonError` 。

**x 必须是单字符字符串，即len(x) == 1**

::

    >> ord('N')
    < 78 >
    >> ord('NZ')
    in '<shell>' + 4 :
        PythonError : ord() expected a character, but string of length 2 found


builtins.hex(x: integer) -> string
##################################

返回以'0x'开头的 x 的十六进制形式。

::

    >> hex(726)
    '0x2d6'


builtins.new(type: struct_type, default_list: array={}) -> object
#################################################################

实例化 struct 类型，返回 struct 对象。

:code:`default_list` 是 *可选* 的。若不提供 :code:`default_list` ，则返回的对象的所有属性都为 **null** 若提供 :code:`default_list` ，则会 **按照struct_type属性的顺序**  依次初始化。

** default_list 的长度必须等于 struct_type 成员的数量！ **

::

    >> struct Person is
    ..      name
    ..      age
    .. end
    >> new(Person)
    <struct 'Person' object at 0x339e520> -> {
            name : null
            age : null
    }
    >> new(Person, {'Nezha', 3})
    <struct 'Person' object at 0x339e0a0> -> {
            name : 'Nezha'
            age : < 3 >
    }
    >>
    >> new(Person, {'Nezha'})
    in '<shell>' + 8 :
            TypeError : struct 'Person' initialize missing 2 required argument(s) : (name, age)
    >>
    >> new(Person, {'Nezha', 3, 80})
    in '<shell>' + 12 :
            TypeError : struct 'Person' initialize takes 2 argument(s) but 3 were given
    >>


builtins.len(x: longish) -> integer
###################################

返回 longish对象 x 的长度。


builtins.equal(a: any, b: any) -> boolean
#########################################

比较x, y是否相等。**比较的对象是两者的地址**。

但是对于 string, integer 可以直接比较其内容 *(float 不可以)*。

::

    >> equal('Nezha', 'NEZHA')
    false
    >> equal('Nezha', 'Nezha')
    true


builtins.equal_type(a: any, b: any) -> boolean
##############################################

比较x, y的类型。

::

    >> equal_type(726, 3)
    true
    >> equal_type({1}, {2, 3})
    true


builtins.array(size: integer) -> array
######################################

返回一个长度为 **size** 的数组。其内容被初始化为 **null** 。

::

    >> array(3)
    {null, null, null}


builtins.isinstance(obj: any, type: struct_type) -> boolean
##############################################################

返回 :code:`obj` 是否是 :code:`type` 类型的对象， **一般用于 struct 类型和对象的比较**。

::

    >> isinstance(new(Person), Person)
    true
    >> isinstance(0, Person)
    false


builtins.str(x: any) -> string
##############################

返回 :code:`x` 的 **字符串形式** 。

::

    >> str(726)
    '726'
    >> str({726, 3})
    '{< 726 >, < 3 >}'
    >> str(new(Person))
    '<struct 'Person' object at 0x33aba00> -> {
            name : null
            age : null
    }'
    >> str(Person)
    '<struct 'Person' at 0x3393b20>'
    >>


builtins.int(x: number) -> integer
##################################

将 x 转换成整数。

::

    >> int(3.0)
    < 3 >
    >> int(-10)
    < -10 >


builtins.repr(x: any) -> string
###############################

返回 :code:`x` 的 **描述(repr)** 形式。repr形式一般被在REPL环境中输出， **请留意与 str(...) 的区别** 。

::

    >> repr(726)
    '< 726 >'
    >> str(726)
    '726'

builtins.open(fp: string, mode: string) -> iobuffer_t
#####################################################

打开一个文件，根据 :code:`mode` 返回一个相对应模式的IO对象。


builtins.addr(obj: any) -> integer
##################################


builtins._get_ccom() -> CCOM_T
##############################


builtins.fnum(num: number) -> fast_number
#########################################


builtins.type(obj: any) -> integer
##################################


