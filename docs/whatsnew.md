# AIL 2.2 Klee 版本更新

AIL 2.2 带来了更为详细的语法错误信息，并提高了整体的稳定性。

## == 更新内容 ==

### 一、适配 Python 3.10

AIL 2.2 版本将开始适配 Python 3.10 的部分功能，源码上会在尽可能兼容 Python 3.7 的基础上进行针对 Python 3.10 的特性的优化。

Python 3.10 版本更新说明：
[py3.10](https://docs.python.org/zh-cn/3/whatsnew/3.10.html)


### 二、更清晰的语法错误提示

新的 AIL 2.2 带来了更为清晰详细的语法错误提示信息。新增加的语法提示包括但不仅限于下面的内容：

#### 错误位置指示
新的 AIL 版本中，当出现语法错误时，AIL 将会给出错误的大致位置：

```python
>> a = match x {}
  File "<shell>", line 1
    a = match x {}
                 ^
SyntaxError: match body cannot be empty
```


#### 括号配对错误提示
新的 AIL 版本中，将对配对错误的括号给出提示：

```python
>> a = (1, 2]
  File "<shell>", line 1
    a = (1, 2]
             ^
SyntaxError: closing parenthesis ']' does not match opening parenthesis '(' (at line 1, col 6)
```

#### 字符串未结束提示
新的 AIL 版本中，未结束的字符串将会给出更详细的提示详细：

```python
>> name = 'klee
  File "<shell>", line 1
    name = 'klee
               ^
SyntaxError: unterminated string literal (detected at line 1)
```


### 三、标准库更新

`maptools` 模块新增 `xmapwith`, `traverse` 函数。


### 四、其他更新内容：
#### 1. AIL shell 中增加 commit id 和 branch 的显示

```python
AIL 2.2 Klee alpha 2 [727] (2.2/d24235a) (Python 3.8.0 (default, Dec  5 2019, 10:53:43)
[Clang 8.0.7 (https://android.googlesource.com/toolchain/clang b55f2d4ebfd35bf6)
Type 'help(...)', '$help', 'copyright()', 'python_copyright()' to get more information, 'exit()' to exit.

>> 
```
#### 2. 增加 `not in` 运算符

`not in` 运算符可以用于快速判断某元素是否存在于一个可迭代对象中：
```python
>> knights_of_favonius = ['Jean', 'Kaeya', 'Eula', 'Amber', 'Rosaria', 'Klee']
>> 'Klee' not in knights_of_favonius
False
>> 'Diona' not in knights_of_favonius
True
>>
>> 1 not in [1, 2, 4, 8, 16]
False
>> 'a' not in 'Jean'
False
>>
```

***注意：***
相比于 `not ... in ...` 表达式，`not in` 作为一个运算符存在，相比前者，使用 `not in` 运算符可以提高程序的执行效率。


### 五、重大 BUG 修复与优化
1. 修复 |= 运算符解析异常问题
2. 修复 not 表达式引导的表达式解析问题
3. 修复 复合下标运算表达式(如 `x[1][2]`) 的解析问题
4. 优化 下标、成员访问、调用三个表达式的解析，提高稳定性

