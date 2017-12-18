# -*- coding=utf-8 -*-
"""
author: Red.Guan
modified: 2017.12.19
"""

import json
import time
import collections

import requests
from Spider.config import *


class LoadingError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class Spider(object):
    def __init__(self):
        self.share_every_page = 60
        self.fans_every_page = 24
        self.follower_every_page = 24

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
                "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/48.0.2564.116 Safari/537.36",
            }

    def get_usr_shares(self, uid, pubshare_count):
        """
        :param pubshare_count:  用户分享文件数量
        :param fans_count: 用户粉丝数，用于计算权重
        """

        if int(pubshare_count) == 0:
            return []
        if pubshare_count > 120:  # 一次爬取太多会遭到ip屏蔽
            pubshare_count = 120
        filelist = []
        file_path1 = r'http://pan.baidu.com/share/link?shareid={}&uk={}'
        file_path2 = r'http://pan.baidu.com/s/{}'

        for i in range(pubshare_count // self.share_every_page + 1):
            url = URLs.share_url.format(i * self.share_every_page, self.share_every_page, uid)
            share_info = json.loads(requests.get(url, headers=Spider._header(uid)).text)
            # 信息加载失败(请求发送太快)，需要重新把uid放入待爬取队列中
            if share_info['errno'] is not 0:
                raise LoadingError('    [ERROR]:获取用户分享失败')

            for s in share_info['records']:
                # note: 有些键不存在，所以需要用dict.get(),而不能使用dict[]形式
                shorturl, shareid, files = s.get('shorturl'), s.get('shareid'), \
                                           s.get('filelist') if s.get( 'filelist') else []
                for f in files:
                    if shorturl or shareid:
                        path = file_path2.format(shorturl) if shorturl else file_path1.format(shareid, uid)
                    else:
                        continue
                    filelist.append(
                        {'title': f.get('server_filename'), 'url': path, 'size': f.get('size'), 'dir': f.get('isdir')})
        return filelist

    def get_usr_fans(self, uid, fans_count):
        """
        :param uid:  正在请求的用户uid
        :param headers:  http请求头
        :return: 粉丝们的uid
        """
        if fans_count == 0:
            return []
        # 根据观察，当粉丝数大于2400时，最多只能获得2400个粉丝信息,这里只需要获取少了粉丝信息,因为这个响应会很慢
        if int(fans_count) > 24:
            fans_count = 24
        fanslist = list()

        for i in range(fans_count // self.fans_every_page + 1):
            url = URLs.fans_url.format(i * self.fans_every_page, self.fans_every_page, uid)
            fans_info = json.loads(requests.get(url, headers=Spider._header(uid)).text)
            if int(fans_info['errno']) is not 0:
                raise LoadingError('    [ERROR]:获取粉丝信息失败')

            fans = fans_info['fans_list'] if fans_info['fans_list'] else []
            for fan in fans:
                fanslist.append({'uid': str(fan['fans_uk']), 'total_follow': fan['follow_count'],
                                 'total_fans': fan['fans_count'], 'total_share': fan['pubshare_count']})
        return fanslist

    def get_usr_follower(self, uid, follower_count):
        """
        :param uid:  正在请求的用户uid
        :param follower_count:  用户的订阅数
        :param headers:  http请求头
        :return:
        """
        if follower_count == 0:
            return []
        if follower_count > 24 * 5:
            follower_count = 24 * 5
        follow_list = list()

        for i in range(int(follower_count) // self.follower_every_page + 1):
            url = URLs.follow_url.format(i * self.follower_every_page, self.follower_every_page, uid)
            follow_info = json.loads(requests.get(url, headers=Spider._header(uid)).text)
            if int(follow_info['errno']) is not 0:
                raise LoadingError('    [ERROR]:获取订阅信息失败')

            follows = follow_info['follow_list'] if follow_info['follow_list'] else []
            for f in follows:
                follow_list.append({'uid': str(f['follow_uk']), 'total_follow': f['follow_count'],
                                   'total_fans': f['fans_count'], 'total_share': f['pubshare_count']})
        return follow_list

    def get_usr_info(self, uid):
        """
        :param uid:
        :return:
        """
        url = URLs.info_url.format(uid)
        try:
            infos = json.loads(requests.get(url, headers=Spider._header(uid)).text)
            total_shares = infos['user_info']['pubshare_count']  # 获得分享文件数
            total_followers = infos['user_info']['follow_count']   # 获得订阅人数
            total_fans = infos['user_info']['fans_count']  # 获得粉丝人数
            # resource_weight = int(math.sqrt(int(total_fans+total_shares))) # 计算该用户资源权重

            usr_shares = self.get_usr_shares(uid, total_shares)
            usr_fans = self.get_usr_fans(uid, total_fans)
            usr_follows = self.get_usr_follower(uid, total_followers)

            return usr_shares, usr_fans, usr_follows
        except LoadingError as le:
            print('----',le)
            return [[]]*3
        except Exception as e:
            print('----',e)
            return [[]]*3

    def run(self, seed_uid):
        newq = collections.deque()
        oldq = collections.deque()
        USR_INFO = collections.namedtuple('USR_INFO', ['shares', 'fans', 'follows'])
        newq.append(seed_uid)
        total_uids = 0
        try:
            while total_uids <= 1000 and len(newq) != 0:
                uid = newq.popleft()
                if uid in oldq:
                    continue
                print('Getting the information from user \'%s\', Total unseen uids is %d and total seen uids is %d '%(uid,len(newq),len(oldq)))

                usr_info = USR_INFO(*self.get_usr_info(uid))

                if usr_info.fans or usr_info.follows or usr_info.shares:
                    oldq.append(uid)
                    [newq.append(f['uid']) for f in usr_info.fans if f['total_share'] ]     # or f['total_follow']>20
                    [newq.append(f['uid']) for f in usr_info.follows if f['total_share'] ]  # or f['total_fans']>20
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