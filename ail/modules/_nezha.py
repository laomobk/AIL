# A info of a movie NEZHA

from ail.core.aobjects import convert_to_ail_object
from ail.objects.struct import new_struct_object
from ail.objects.null import null

_IS_AIL_MODULE_ = True


_aobing_info = {
    'name': convert_to_ail_object('AoBing'),
    'age': convert_to_ail_object('3'),
    'location': convert_to_ail_object('龙宫')
}

_nezha_info = {
    'name': convert_to_ail_object('Nezha'),
    'age': convert_to_ail_object(3),
    'friend': convert_to_ail_object(
        new_struct_object('Aobing', null, _aobing_info, _aobing_info.keys()),
        ),
    'location': convert_to_ail_object('陈塘关')
}


_AIL_NAMESPACE_ = {
    'NAME': 'Nezha',
    'DATE': '2019/7/26',
    'BOX_OFFICE_IN_CHINA': '50.13亿',
    'NEZHA': new_struct_object('NEZHA', null, _nezha_info, _nezha_info.keys())
}
