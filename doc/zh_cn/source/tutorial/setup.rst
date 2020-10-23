搭建AIL运行环境
===============

AIL使用Python编写，正因如此，AIL的运行环境配置十分简单。

前期准备
########

AIL需要依赖Python运行，因此在安装AIL之前，请先配置好Python环境。

具体配置方法就不多赘述，可参见Python的文档： 
**https://docs.python.org/3/tutorial/index.html**

下载AIL
#######

AIL目前在Ail-Lang这个Github仓库中进行维护。下载AIL，就像克隆其他仓库一般，克隆AIL-Lang仓库：

**AIL仓库地址：https://github.com/laomobk/Ail-lang**

*(本教程并不涉及过多git操作的内容，若没有使用过git (或者github)，可以先进行相关的了解)*

在进行克隆之前，确保你的机器上已经安装并配置好好git环境。

打开git bash，输入:

::
    
    git clone https://github.com/laomobk/Ail-lang.git


不出意外，AIL的源码将会克隆到你的电脑上。


安装AIL
#######

AIL的安装十分简便。在AIL源码的根目录下，输入

::

    python setup.py install


在终端中输入: :code:`ail` ，若能成功进入到AIL的交互环境，则说明安装成功。

