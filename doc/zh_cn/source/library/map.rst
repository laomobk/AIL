
map -- 提供基本 HashMap 操作
~~~~~~~~~~~~~~~~~~~~~~~~~~~~


map模块用于 *(暂时)* 填补AIL语言不支持map数据类型的空缺。

 *本文中的REPL表示均事先加载了 map 模块*

type hash_map
#############

hash_map 类型 **(属于内置struct类型，不可被初始化)** 用于表示一个散列映射表

hash_map.put(key: hashable, value) 
##################################

hash_map.put用于在hash_map对象中放入 **键-值对** 。若 key 不可进行hash化，则会抛出 **UnhashableError** 。

hash_map.get(key: hashable, default=null) -> object 
###################################################

hash_map.get用于在hash_map对象中根据key来获取相对应的value，若key不存在，则返回default值 *(默认是null)* 。若key不可进行hash化，则抛出 **UnhashableError** 。


::
    
    >> m = map()
    >> m.put('NezhaAge', 3)
    >> m.get('NezhaAge')
    < 3 >
    >> m.get('foo')
    >> // null


map.map() -> hash_map
#####################

该函数返回一个空的hash_map对象

