基本输入输出语句
################

对于一个算法，有输入，也要有输出。AIL提供了一种简单的向屏幕打印内容和从键盘接收输入的方式。


print 语句
##########

想要简单地在屏幕上输出内容，可以使用 print 语句。

print语句十分简单，方便：:code:`print` 关键字后，加上你所想要输出的内容。要注意，这些内容必须是AIL的数据结构或者是存在的变量。

下面是一些合法和不合法（注释标出）的输出语句：

::

    print 'NEZHA'
    print 123
    print 1 + 2 + 3  // expression also be supported!
    print 'A' + ' and ' + 'B'

    a = [1, 2, 'NEZHA']
    print a     // a is a variable!
    print a[0]  // a[0] is a number!

    print x     // x is not a variable (not defined)


对于输出多个项，必须要使用 :code:`;` 隔开。

::

    >> print 'Nezha is'; age; 'years old'
    Nezha is 3 years old


其中，分隔符默认是 **一个空格** 。


input 语句
#########

想要简单地接收输入，可以使用 :code:`input` 语句。

像 :code:`print` 语句一样，input 语句也十分简单：:code:`input` 后接着就是 *提示* 部分，接着就是用于存储输入的变量。

这个变量可以是先前未定义过的，若先前定义了该变量，则会覆盖先前的内容。

::

    >> input 'What is your name: '; name
    What is your name: Nezha
    >> name
    'Nezha'
    >> input 'What is your name: '; name
    What is your name: Aobing
    >> name
    'Aobing'


*若没有接收变量，则只会简单提示输入，输入的内容会被丢弃*

*（若要更高级的输入需求，则应该使用console对象）*
