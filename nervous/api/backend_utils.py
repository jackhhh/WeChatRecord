from api import getdata
import traceback


def verify_wx_name(wx_name):
    try:
        params = {'wx_name': wx_name}
        d = getdata.get_dict('/weixin/v1/users', params)
        return d['data'][0]['wx_name'] == wx_name
    except Exception as e:
        traceback.print_exc()
        return None
