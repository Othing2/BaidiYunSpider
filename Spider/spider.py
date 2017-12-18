"""
通过发送相应请求可以获得用户的分享数据(json类型)、粉丝数据(json 类型)、订阅数据(json类型)、以及用户的概况信息(json类型)
用户的分享数据，其结构可以参考./text/share_list.txt
用户的粉丝数据，其结构参考./text/fans_list.txt
用户的订阅数据，其结构参考./text/follow_list.txt
用户的总体概括信息，可以参考./text/info_list.txt

出现的问题：
    1、分享数、粉丝数、订阅数太多的话，在连续请求的时候，会出现屏蔽IP的情况
        解决方法：在多进程(多线程中)、多代理IP服务时，在队列中保存 (uid, start_page, total_page,time)[命名元组]
"""
import json, math
import time
import collections

import requests
from pymongo import MongoClient
from .config import *




class LoadingError(Exception):
    def __init__(self, msg):
        self.msg = msg
    def __str__(self):
        return repr(self.msg)

info_url = r'http://pan.baidu.com/pcloud/user/getinfo?bdstoken=null&query_uk={}&channel=chunlei&clienttype=0&web=1'
share_url = r'http://pan.baidu.com/pcloud/feed/getsharelist?category=0&auth_type=1&request_location=share_home&start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'
fans_url = r'http://pan.baidu.com/pcloud/friend/getfanslist?start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'
follow_url = 'http://pan.baidu.com/pcloud/friend/getfollowlist?start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'

def get_usr_shares(uid, pubshare_count, headers):
    """
    :param pubshare_count:  用户分享文件数量
    :param fans_count: 用户粉丝数，用于计算权重
    """
    global share_url

    if int(pubshare_count)==0:
        return []
    if pubshare_count > 120:     # 一次爬取太多会遭到ip屏蔽
        pubshare_count = 120
    share_every_page, filelist = 60, []
    file_path1 = r'http://pan.baidu.com/share/link?shareid={}&uk={}'
    file_path2 = r'http://pan.baidu.com/s/{}'

    for i in range(pubshare_count // share_every_page + 1):
        url = share_url.format(i*share_every_page,share_every_page,uid)
        share_info = json.loads(requests.get(url, headers=headers).text)
        # 信息加载失败(请求发送太快)，需要重新把uid放入待爬取队列中
        if share_info['errno'] is not 0:
            raise LoadingError('    [ERROR]:获取用户分享失败')

        for s in share_info['records']:
            #note: 有些键不存在，所以需要用dict.get(),而不能使用dict[]形式
            shorturl, shareid, files=s.get('shorturl'),s.get('shareid'),s.get('filelist') if s.get('filelist') else []
            for f in files:
                if shorturl or shareid:
                    path =  file_path2.format(shorturl) if shorturl else file_path1.format(shareid, uid)
                else:
                    continue
                filelist.append({'title':f.get('server_filename'), 'url':path, 'size':f.get('size'), 'dir':f.get('isdir')})
    return filelist

def get_usr_fans(uid, fans_count, headers):
    """
    :param uid:  正在请求的用户uid
    :param headers:  http请求头
    :return: 粉丝们的uid
    """
    global fans_url

    if fans_count == 0:
        return []
    # 根据观察，当粉丝数大于2400时，最多只能获得2400个粉丝信息,这里只需要获取少了粉丝信息,因为这个响应会很慢
    if int(fans_count) > 24:
        fans_count = 24
    fans_every_page, fanslist= 24, []

    for i in range(fans_count//fans_every_page + 1):
        url = fans_url.format(i*fans_every_page,fans_every_page,uid)
        fans_info = json.loads(requests.get(url, headers=headers).text)
        if int(fans_info['errno']) is not 0:
            raise LoadingError('    [ERROR]:获取粉丝信息失败')

        fans = fans_info['fans_list'] if fans_info['fans_list'] else []  #防止fans_list不存在，使得fans_list = None (不可迭代)
        for fan in fans:
            fanslist.append({'uid':str(fan['fans_uk']), 'total_follow':fan['follow_count'],
                             'total_fans':fan['fans_count'], 'total_share':fan['pubshare_count']})
    return fanslist

def get_usr_follower(uid, follower_count, headers):
    """
    :param uid:  正在请求的用户uid
    :param follower_count:  用户的订阅数
    :param headers:  http请求头
    :return:
    """
    global follow_url

    if follower_count == 0:
        return []
    if follower_count>24*5:
        follower_count = 24*5
    follower_every_page, followlist = 24, []

    for i in range(int(follower_count) // follower_every_page + 1):
        url = follow_url.format(i * follower_every_page, follower_every_page, uid)
        follow_info = json.loads(requests.get(url,headers=headers).text)
        if int(follow_info['errno']) is not 0:
            raise LoadingError('    [ERROR]:获取订阅信息失败')

        follows = follow_info['follow_list'] if follow_info['follow_list'] else []
        for f in follows:
            followlist.append({'uid':str(f['follow_uk']), 'total_follow':f['follow_count'],
                             'total_fans':f['fans_count'], 'total_share':f['pubshare_count']})
    return followlist

def get_usr_info(uid):
    """
    :param uid:
    :return:
    """
    global info_url

    headers = {
        "Accept": "application/json, text_parse/javascript, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, sdch",
        "Accept-Language": "zh-CN,zh;q=0.8",
        "Cache-Control": "max-age=0",
        "Connection": "keep-alive",
        "Cookie": "",
        "Host": "pan.baidu.com",
        "Referer": "http://pan.baidu.com/share/home?uk={}&view=share".format(uid),
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36",
    }
    url = info_url.format(uid)
    try:
        infos = json.loads(requests.get(url, headers=headers).text)
        total_shares = infos['user_info']['pubshare_count']  # 获得分享文件数
        total_followers = infos['user_info']['follow_count']   # 获得订阅人数
        total_fans = infos['user_info']['fans_count']  # 获得粉丝人数
        # resource_weight = int(math.sqrt(int(total_fans+total_shares))) # 计算该用户资源权重

        usr_shares = get_usr_shares(uid,total_shares,headers)
        usr_fans = get_usr_fans(uid,total_fans,headers)
        usr_follows = get_usr_follower(uid,total_followers,headers)

        return usr_shares, usr_fans, usr_follows
    except LoadingError as le:
        print('----',le)
        return [[]]*3
    except Exception as e:
        print('----',e)
        return [[]]*3

def run(seed_uid):
    newq = collections.deque()
    oldq = collections.deque()
    USR_INFO = collections.namedtuple('USR_INFO',['shares','fans','follows'])
    newq.append(seed_uid)
    total_uids = 0
    try:
        while total_uids <= 1000 and len(newq)!=0:
            uid = newq.popleft()
            if uid in oldq:
                continue
            print('Getting the information from user \'%s\', Total unseen uids is %d and total seen uids is %d '%(uid,len(newq),len(oldq)))

            usr_info = USR_INFO(*get_usr_info(uid))

            if usr_info.fans or usr_info.follows or usr_info.shares:
                oldq.append(uid)
                [ newq.append(f['uid']) for f in usr_info.fans if f['total_share'] ]     # or f['total_follow']>20
                [ newq.append(f['uid']) for f in usr_info.follows if f['total_share'] ]  # or f['total_fans']>20
                if usr_info.shares:
                    total_uids += 1
                    table_shares.insert({'uid': uid, 'sharelist': usr_info.shares})
                if usr_info.fans:
                    table_fans.insert({'uid': uid, 'fanslist': usr_info.fans})
                if usr_info.follows:
                    table_follows.insert({'uid': uid, 'followlist': usr_info.follows})
            time.sleep(30)
    except Exception as e:
        print('    [ERROR]:',e)
    finally:
        table_seen_uid.insert({'uids':oldq})
        table_unseen_uid.insert({'uids':newq})






if __name__ == '__main__':
    uids = ['697008088','3660825403','775105216','154098367','491745132']
    # table_shares.remove()
    # table_fans.remove()
    # table_follows.remove()
    usr_shares, usr_fans, usr_follows = get_usr_info(uids[2])
    [print(us) for us in usr_shares if us]
    [print(uf) for uf in usr_fans if uf]
    [print(uf) for uf in usr_follows if uf]
    # print('Starting Time:------------------%s----------------' % time.ctime())
    # run(uids[2])
    # print('Ending Time:------------------%s----------------' % time.ctime())














