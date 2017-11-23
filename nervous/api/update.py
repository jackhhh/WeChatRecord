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

    # d = getdata.get_dict('wx/opensearchapi/content_list', paras)

    # totnum = d['returnData']['total']
    # ind = (d['returnData'])['items']
    # add_items(ind)
    # totnum -= 10
    # cnt = 10
    # while totnum > 0:
    #     paras['start'] = cnt
    #     d = getdata.get_dict('wx/opensearchapi/content_list', paras)
    #     d1 = (d['returnData'])['items']
    #     add_items(d1)
    #     totnum -= 10
    #     cnt += 10

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
    # try:
    #     paras = {'wx_name': account}
    #     d = getdata.get_dict('wx/opensearchapi/nickname_order_now', paras)
    #     return float(d['returnData']['items'][0]['wci'])
    # except IndexError:
    #     print 'WCI fetching for %s fails, trying brute force...' % account
    #     url = 'http://www.gsdata.cn/query/wx?q=%s&search_field=2' % account
    #     text = requests.get(url, timeout=7).text
    #     g = re.search(r"class=\"hm\">\r\n(.*?)<", text)
    #     return float(g.group(1))


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

    # day_string = get_time_string_before_n_days(n)
    # paras = {
    #     'wx_name': account,
    #     'beginDate': day_string,
    #     'endDate': day_string
    # }
    # d = getdata.get_dict('wx/opensearchapi/nickname_order_total', paras)
    # res = d['returnData']
    # dic = {
    #     'date': get_date_object_before_n_days(n),
    #     'likes': res.get('likenum_total', 0),
    #     'views': res.get('readnum_total', 0),
    #     'articles': res.get('url_num_total', 0),
    # }
    # # Maybe gsdata hasn't got the data ...
    # if dic['views'] == 0:
    #     return False

# 这个函数是更新前1-9天的数据，循环调用第n天数据的那个函数。老接口不支持返回当天的wci，要自己算，所以被淘汰了
def update_official_account_daily_nums(account):
    for i in xrange(1, 9):
        update_official_account_nums_before_n_days(account, i)

    # account_instance = database.models.OfficialAccount.objects \
    #     .get(wx_id=account)
    # for i in xrange(1, 9):
    #     date = get_date_object_before_n_days(i)
    #     ret = update_official_account_nums_before_n_days(account, i)
    #     if not ret:
    #         continue
    #     record = database.models.AccountRecord.objects \
    #         .get(account=account_instance, date=date)

    #     def tz_time_before_n_days(i):
    #         date = get_date_object_before_n_days(i)
    #         return database.gsdata_utils.tz_time_from_naive_time(
    #             datetime.datetime(date.year, date.month, date.day)
    #         )

    #     end_time = tz_time_before_n_days(i - 1)
    #     start_time = tz_time_before_n_days(i)
    #     articles = database.models.Article.objects \
    #         .filter(official_account_id=account_instance.id) \
    #         .filter(posttime__lte=end_time) \
    #         .filter(posttime__gte=start_time)
    #     max_r, max_z, r, z = 0, 0, 0, 0
    #     for article in articles:
    #         max_r = max(max_r, article.views)
    #         max_z = max(max_z, article.likes)
    #         r = r + article.views
    #         z = z + article.likes
    #     record.wci = calculate_wci(r, max_r, z, max_z, articles.count())
    #     record.save()

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

    # paras = {'wx_name': account}
    # d = getdata.get_dict('wx/opensearchapi/nickname_order_total', paras)
    # res = d['returnData']
    # res_dic = {
    #     'likes_total': res['likenum_total'],
    #     'views_total': res['readnum_total'],
    #     'wci': get_wci(account)
    # }
    # database.gsdata_utils.update_account_nums(account, res_dic)


def update_all(account):
    try:
        update_official_account(account)
        update_official_account_nums(account)
        update_official_account_daily_nums(account)
    except (KeyError, IndexError):
        print u'update of account %s failed due to gsdata error' % account
    except socket.timeout:
        print u'update of account %s failed due to network error' % account
