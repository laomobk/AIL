基本控制流
##########

AIL提供了几种控制流语句来改变程序执行的顺序。


if-elif-else语句
================

条件判断语句可以使得程序根据某个条件来选择执行的方向。语法如下：

.. code::

    'if' condition '{
        stmt*
    '}' ['elif' condition '{' 
        stmt*
    '}']* ['else' '{'
        stmt*
    '}']?


其中，if 后跟的语句块在 if 后的条件为 **True** 时被执行，执行完后将跳转出 **整个语句** 。否则将跳转至 elif 或者 else 块。其中，elif 可以有多条，后仍然接一个条件，条件为 **True** 时，执行其后跟的语句块，执行完后跳出整个语句，否则继续检测下一个elif。如果有 else ，且if, elif给出的条件均为 **False** ，则 else 语句块被执行。

格式要求
~~~~~~~~

对于该语句，请将 :code:`{` 写在 *condition* 之后，且在同一行，而 :code:`}` 写在 elif 和 else 之后（如果有的话）），且在同一行。


while语句
=========

while语句可以对语句块内容进行循环执行操作。其语法如下：

.. code::

    'while' condition '{'
        stmt*
    '}'


while在流程上属于 **先判断，后执行** 型语句。

格式要求
~~~~~~~~

对于该语句，:code:`{` 要与 *condition* 在同一行。


for语句
=======

与while类似，for语句也多用于实现循环执行。其语法如下：

.. code::

    'for' '(' [expr [',' expr]*]? ';' condition ';' [expr [',' expr]*]? ')' '{'
        stmt*
    '}'


for除语句块部分外，由三个部分组成： *Initialize* , *Condition* , *Update* 

下面是三个部分之间的关系：

.. code::

            |
            V
        Initialize
            |<------|
            |       |
            V       |
        Condition   |
            |       |
            V       |
        [For Body]  |
            |       |
            V       |
          Update    |
            |_______|


对于for语句，这三个部分都是 **可选** 的，也就是说，这三个部分可以全部留空（但是要保留 :code:`;` ），这时候的for语句头是: :code:`for (;;) ...` 。这个时候的for循环相当于 :code:`while true ...` 。实际上，只要 *Condition* 部分是空时，就可以达到这种效果。除此之外，如果将 *Initialize* 部分留空，则不会有初始化行为；将 *Update* 留空，则不会有更新行为。


格式要求
~~~~~~~~

对于for语句块的 :code:`{` ，要和 :code:`for ...` 在同一行。


break与continue
===============

break语句用于跳出循环，包括while循环和for循环。当执行到break语句时，程序将跳转到离开循环的下一条语句进行。

continue语句用于 **跳过** 本次循环（注意不是跳出）。当执行到continue语句时，将跳过该语句下面的内容，会到循环的判断部分，如果是for循环，则仍会执行 *Update* 部分。

break语句和continue语句在try语句中被执行时，finally部分的内容仍然会被执行。


try-catch-finally语句
=====================

try-catch-finally语句（以下简称try语句）用于进行异常捕获或者用于执行一些必须要执行的代码。语法如下：

.. code::
    
    'try' '{'
        stmt*
    '}' 'catch' NAME '{'
        stmt*
    '}']? 'finally' '{'
        stmt*
    '}'

需要注意的是，该语句可以选择是否有catch或finally，也可以两者一起，当两者都有时， **finally语句在catch下面** 。

try 语句块内的代码，通常是可能会引发异常的代码。当try内又异常被抛出后， *如果有catch块* 则程序会立即跳转到catch块内，并且将被捕获的异常赋值给 *NAME* 变量。

而finally保证了无论是否有异常发生，块内的代码总是会被执行。

.. code::

    try {
        0 / 1
    } finally {
        print 'here is finallyA'
    }

    try {
        1 / 0
    } finally {
        print 'here is finallyB'
    }



执行结果：

.. code::
    
    here is finallyA
    here is finallyB
    Traceback (most recent call last):
      File 'test_finally.ail', line 7, in <main>
        1 / 0
    ZeroDivisionError: division by zero


可以看到，无论异常是否发生，即使没有catch进行捕获，finally的内容让仍然会被执行。

