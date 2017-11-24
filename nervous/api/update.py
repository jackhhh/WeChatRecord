# -- coding: utf-8 --
import datetime
import re
import requests
import socket
import time
import math
import database.gsdata_utils
import database.models
from api import getdata


def get_time_string_before_n_days(n):
    seconds_of_day = 60 * 60 * 24
    target_time = time.localtime(time.time() - n * seconds_of_day)
    return time.strftime('%Y-%m-%d', target_time)


def get_date_object_before_n_days(n):
    return datetime.date.today() - datetime.timedelta(days=n)


def get_time_string_before_month():
    return get_time_string_before_n_days(30)


def get_time_string_now():
    return get_time_string_before_n_days(0)


def add_items(dic):
    for temp in dic:
        temp['official_account_name'] = temp['name']
        temp['description'] = temp['digest']
        temp['views'] = temp['read_count']
        temp['likes'] = temp['like_count']
        temp['avatar_url'] = temp['picurl']
        temp['update_time'] = get_time_string_now()
        database.gsdata_utils.add_article(temp)

# 这个函数其实是添加文章 1个月的
def update_official_account(account):
    print 'updating official account: %s' % account

    paras = {
        'end_date': get_time_string_now(),
        'page': 1,
        'per-page': 50,
        'start_date': get_time_string_before_month(),
        'wx_name': account
    }

    check_eof_id = 'empty'
    d = getdata.get_dict('/weixin/v1/articles', paras)
    ind = d['data']

    while ind[0]['id'] != check_eof_id:
        check_eof_id = ind[0]['id']
        add_items(ind)
        paras['page'] += 1
        d = getdata.get_dict('/weixin/v1/articles', paras)
        ind = d['data']

# 这个函数获得的wci是最新的 当前的
def get_wci(account):
    try:
        paras = {'wx_name': account}
        d = getdata.get_dict('/weixin/v1/users', paras)
        return d['data'][0]['wci']
    except IndexError:
        print 'WCI fetching for %s fails, trying brute force...' % account
        url = 'http://www.gsdata.cn/query/wx?q=%s&search_field=2' % account
        text = requests.get(url, timeout=7).text
        g = re.search(r"class=\"hm\">\r\n(.*?)<", text)
        return float(g.group(1))


def get_official_account_nums_before_n_days(account, n):
    day_string = get_time_string_before_n_days(n)
    paras = {
        'start_date': day_string,
        'wx_name': account
    }
    d = getdata.get_dict('/weixin/v1/users/rank-days', paras)
    if d['data'] == []:
        return False
    res = d['data'][0]
    return res

# 这个函数虽然请求字段里有start_date 但是实际上只返回start_date当天的数据 所以可以视为请求第n天前的数据
def update_official_account_nums_before_n_days(account, n):
    res = get_official_account_nums_before_n_days(account, n)
    
    # Maybe gsdata hasn't got the data ...
    if res == False:
        return False

    dic = {
        'date': get_date_object_before_n_days(n),
        'likes': res.get('likenum_all', 0),
        'views': res.get('readnum_all', 0),
        'articles': res.get('url_num', 0),
        'wci': res.get('wci', 0)
    }

    database.gsdata_utils.add_account_record(account, dic)
    return True

# 这个函数是更新前1-9天的数据，循环调用第n天数据的那个函数。老接口不支持返回当天的wci，要自己算，所以被淘汰了
def update_official_account_daily_nums(account):
    for i in xrange(1, 9):
        update_official_account_nums_before_n_days(account, i)

# 这个函数老接口可以调用该公众号总共的阅读数和点赞数，新接口已经没有这个返回值了，所以这里的操作是求和7天的阅读数和点赞数，变量名和数据库里的键名没有改
def update_official_account_nums(account):
    likes_total = 0
    views_total = 0
    for i in xrange(1, 7):
        d = get_official_account_nums_before_n_days(account, i)
        if d == False:
            continue
        likes_total += d['likenum_all']
        views_total += d['readnum_all']
    dic = {
        'likes_total': likes_total,
        'views_total': views_total,
        'wci': get_wci(account)
    }
    database.gsdata_utils.update_account_nums(account, dic)


def update_all(account):
    try:
        update_official_account(account)
        update_official_account_nums(account)
        update_official_account_daily_nums(account)
    except (KeyError, IndexError):
        print u'update of account %s failed due to gsdata error' % account
    except socket.timeout:
        print u'update of account %s failed due to network error' % account
