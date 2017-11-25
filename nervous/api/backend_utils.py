from api import getdata
import traceback


def verify_wx_name(wx_name):
    try:
        params = {'wx_name': wx_name}
        d = getdata.get_dict('/weixin/v1/users', params)
        if d['data'] == []:
            return False
        else:
            return True
    except Exception as e:
        traceback.print_exc()
        return None
