# -*- coding=utf-8 -*-
"""
author: Red.Guan
modified: 2017.12.19
"""

import json
import time
import collections
import requests
import math
import gevent
from gevent import monkey, lock
from gevent.queue import Empty, Queue
monkey.patch_all()

from Spider.config import *


class LoadingError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class Spider(object):
    def __init__(self, new_uid_list, old_uid_dict=dict()):
        self.share_every_page = 60
        self.fans_every_page = 24
        self.follower_every_page = 24

        self.Max_Pubshare = 120
        self.Max_Follower = 120
        self.Max_Fans = 24

        self.Max_Uids = 1000
        self.cur = 0

        self.Max_Info_Jobs = 2
        self.Max_Share_Jobs = 6
        self.Max_Follow_Jobs = 2
        self.Max_Fans_JObs = 2

        self.new_uid_q = Queue()
        for uid in new_uid_list:
            self.new_uid_q.put(uid)

        self.new_uid_dict = dict()
        self.old_uid_dict = old_uid_dict
        self.new_shares_dict = dict()
        self.new_fans_dict = dict()
        self.new_follow_dict = dict()

        self.running = True

    @classmethod
    def _header(cls, uid):
        return {
                "Accept": "application/json, text_parse/javascript, */*; q=0.01",
                "Accept-Encoding": "gzip, deflate, sdch",
                "Accept-Language": "zh-CN,zh;q=0.8",
                "Cache-Control": "max-age=0",
                "Connection": "keep-alive",
                "Cookie": "",
                "Host": "pan.baidu.com",
                "Referer": "http://pan.baidu.com/share/home?uk={}&view=share".format(uid),
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                              "(KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36",
            }

    def get_usr_shares(self):
        """

        """
        while self.cur <= self.Max_Uids or len(self.new_shares_dict):

            while not len(self.new_shares_dict):
                if self.running:
                    gevent.sleep(5)
                else:
                    return

            uid, pubshare_count = self.new_shares_dict.popitem()

            if int(pubshare_count) == 0:
                continue
            if pubshare_count > self.Max_Pubshare:  # 一次爬取太多会遭到ip屏蔽
                pubshare_count = self.Max_Pubshare
            file_list = []
            file_path1 = r'http://pan.baidu.com/share/link?shareid={}&uk={}'
            file_path2 = r'http://pan.baidu.com/s/{}'

            for i in range(pubshare_count // self.share_every_page + 1):
                url = URLs.share_url.format(i * self.share_every_page, self.share_every_page, uid)
                share_info = json.loads(requests.get(url, headers=Spider._header(uid), timeout=30).text)
                # 信息加载失败(请求发送太快)，需要重新把uid放入待爬取队列中
                if share_info['errno'] is not 0:
                    print('    [ERROR]:获取用户%s的分享失败' % uid)
                    break
                for s in share_info['records']:
                    # note: 有些键不存在，所以需要用dict.get(),而不能使用dict[]形式
                    shorturl, shareid, _list = s.get('shorturl', ''), s.get('shareid', ''), s.get('filelist', [])
                    for f in _list:
                        if shorturl or shareid:
                            path = file_path2.format(shorturl) if shorturl else file_path1.format(shareid, uid)
                        else:
                            continue
                        file_list.append({'title': f.get('server_filename'), 'url': path,
                                         'size': f.get('size'), 'dir': f.get('isdir')})
            # 存mongo

    def get_usr_fans(self):
        """
        note: 根据观察，当粉丝数大于2400时，最多只能获得2400个粉丝信息,这里只需要获取少了粉丝信息,因为这个响应会很慢
        """
        while self.cur <= self.Max_Uids or len(self.new_fans_dict):

            while not len(self.new_fans_dict):
                if self.running:
                    gevent.sleep(5)
                else:
                    return

            uid, fans_count = self.new_fans_dict.popitem()
            if fans_count == 0:
                continue
            if int(fans_count) > self.Max_Fans:
                fans_count = self.Max_Fans
            fans_list = list()

            for i in range(fans_count // self.fans_every_page + 1):
                url = URLs.fans_url.format(i * self.fans_every_page, self.fans_every_page, uid)
                fans_info = json.loads(requests.get(url, headers=Spider._header(uid), timeout=30).text)
                if int(fans_info['errno']) is not 0:
                    print('    [ERROR]:获取用户 %s 粉丝信息失败' % uid)
                    break
                _list = fans_info.get('fans_list', [])
                for f in _list:
                    self.new_uid_q.put(str(f['fans_uk']))
                    fans_list.append({'uid': str(f['fans_uk']), 'total_follow': f['follow_count'],
                                     'total_fans': f['fans_count'], 'total_share': f['pubshare_count']})
                # 存表

    def get_usr_follower(self):
        """

        """
        while self.cur <= self.Max_Uids or len(self.new_follow_dict):

            while not len(self.new_follow_dict):
                if self.running:
                    gevent.sleep(5)
                else:
                    return

            uid, follower_count = self.new_follow_dict.popitem()
            if follower_count == 0:
                continue
            if follower_count > self.Max_Follower:
                follower_count = self.Max_Follower
            follow_list = list()

            for i in range(int(follower_count) // self.follower_every_page + 1):
                url = URLs.follow_url.format(i * self.follower_every_page, self.follower_every_page, uid)
                follow_info = json.loads(requests.get(url, headers=Spider._header(uid), timeout=30).text)
                if int(follow_info['errno']) is not 0:
                    print('    [ERROR]:获取用户 %s 的订阅信息失败'%uid)
                    break
                _list = follow_info.get('follow_list', [])
                for f in _list:
                    self.new_uid_q.put(str(f['follow_uk']))
                    follow_list.append({'uid': str(f['follow_uk']), 'total_follow': f['follow_count'],
                                       'total_fans': f['fans_count'], 'total_share': f['pubshare_count']})
                # 存表

    def get_usr_info(self):
        """
        获取用户信息（分享数，订阅数，粉丝数）
        """

        while self.cur <= self.Max_Uids:
            try:
                uid = self.new_uid_q.get(block=True, timeout=60)
                if self.old_uid_dict.get(uid):
                    continue

            except Empty:
                self.running = False
                print("No More New Uid! Get_Usr_Info End")
                return
            url = URLs.info_url.format(uid)
            try:
                infos = json.loads(requests.get(url, headers=Spider._header(uid), timeout=30).text)
                total_shares = infos['user_info']['pubshare_count']  # 获得分享文件数
                total_followers = infos['user_info']['follow_count']   # 获得订阅人数
                total_fans = infos['user_info']['fans_count']  # 获得粉丝人数
                _weight = int(math.sqrt(int(total_fans+total_shares)))  # 计算该用户资源权重

                # usr_shares = self.get_usr_shares(uid, total_shares)
                # usr_fans = self.get_usr_fans(uid, total_fans)
                # usr_follows = self.get_usr_follower(uid, total_followers)
                self.new_shares_dict[uid] = total_shares
                self.new_follow_dict[uid] = total_followers
                self.new_fans_dict[uid] = total_fans
                self.old_uid_dict[uid] = _weight
                self.new_uid_dict[uid] = (total_fans, total_followers, total_shares, _weight)

                self.cur += 1
            except LoadingError as le:
                print('>>>>>>>Loading ERROR In Doing %s : \n' % __name__, le)
            except Exception as e:
                print('>>>>>>>ERROR In Doing %s : \n' % __name__, e)

        self.running = False
        # new_uid_dict 需要存表

    def run(self, seed_uid):
        newq = collections.deque()
        oldq = collections.deque()
        newq.append(seed_uid)
        total_uids = 0
        try:
            while total_uids <= self.Max_Uids and len(newq) != 0:
                uid = newq.popleft()
                if uid in oldq:
                    continue
                print('Getting the information from user \'%s\', Total unseen uids is %d and total seen uids is %d '%(uid,len(newq),len(oldq)))

                usr_info = USR_INFO(*self.get_usr_info(uid))

                if usr_info.fans or usr_info.follows or usr_info.shares:
                    oldq.append(uid)
                    [newq.append(f['uid']) for f in usr_info.fans if f['total_share']]     # or f['total_follow']>20
                    [newq.append(f['uid']) for f in usr_info.follows if f['total_share']]  # or f['total_fans']>20
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

    def multi(self):
        g_jobs = list()

        for _ in range(self.Max_Fans_JObs):
            j = gevent.spawn(self.get_usr_fans, uid, fans_count)
            g_jobs.append(j)

        for _ in range(self.Max_Follow_Jobs):
            j = gevent.spawn(self.get_usr_follower, uid, follower_count)
            g_jobs.append(j)

        for _ in range(self.Max_Info_Jobs):
            j = gevent.spawn(self.get_usr_info, uid)
            g_jobs.append(j)

        for _ in range(self.Max_Share_Jobs):
            j = gevent.spawn(self.get_usr_shares, uid, share_count)
            g_jobs.append(j)

        gevent.joinall(g_jobs)
