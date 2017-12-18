"""
通过发送相应请求可以获得用户的分享数据(json类型)、粉丝数据(json 类型)、订阅数据(json类型)、以及用户的概况信息(json类型)
用户的分享数据，其结构可以参考./text/share_list.txt
用户的粉丝数据，其结构参考./text/fans_list.txt
用户的订阅数据，其结构参考./text/follow_list.txt
用户的总体概括信息，可以参考./text/info_list.txt

出现的问题：
    1、分享数、粉丝数、订阅数太多的话，在连续请求的时候，会出现屏蔽IP的情况
        解决方法：在多进程(多线程中)、多代理IP服务时，在队列中保存 {'uid':(share_start, fans_start, follow_start)}
"""
import json, math, sys, time
from collections import deque
import multiprocessing as mp

import requests
from requests import exceptions as es
from pymongo import MongoClient

from Spider.config import *

client = MongoClient()
db = client.BaiduYunPan           #数据库
db_shares = db.shares2     #分享数据表单
db_followers = db.followers   #订阅表单
db_fans = db.fans         #粉丝表单
db_uids = db.uids


class LoadingError(Exception):
    def __init__(self, msg):
        self.msg = msg

    def __str__(self):
        return repr(self.msg)


class BaiduYunSpider:

    def __init__(self, nums, seed_uid, unseen_uids=None, seen_uids=None, start_page=(0,0,0)):
        """
        :type nums:         [int]       待爬取得用户数
        :param seed_uid:    [str]       种子uid
        :param unseen_uids: [deque()]   待爬取得uid队列
        :param seen_uids:   [deuqe()]   已爬取过得uid队列
        :param start_page:  [tuple]     一个uid的起始page
        """
        self.every_pages = 3     # 一次爬取太多会遭到ip屏蔽，这里规定每次只获取3页的数据
        self.share_every_page = 60
        self.follower_every_page = 24
        self.fans_every_page = 24

        self.Fail_cnt = 0
        self.nums = nums
        self.sleep_time = SLEEP_TIME
        self.seed_uid = seed_uid
        self.start_page = start_page
        self.total_uids = 0 if seen_uids is None else len(seen_uids)

        self.unseen = unseen_uids if unseen_uids else deque()
        self.seen = seen_uids if seen_uids else deque()
        if not unseen_uids:
            self.unseen.append({self.seed_uid: START(*self.start_page)})

    def _get_usr_shares(self,uid, total_shares, start, headers):
        """
        :param uid: 用户ID
        :param start:用户分享数据的起始位置
        :param total_shares:  用户分享文件总数量
        """
        if int(total_shares) == 0 or start>=total_shares:
            return [],start
        file_path1 = r'http://pan.baidu.com/share/link?shareid={}&uk={}'
        file_path2 = r'http://pan.baidu.com/s/{}'

        """对于有很多分享文件的用户，需要分段爬取，每次最多爬取self.every_pages*self.share_every_page个文件"""
        pages = self.every_pages if (total_shares-start) >= self.every_pages*self.share_every_page \
            else 1+(total_shares-start)//self.share_every_page

        filelist , new_start = [], start
        for i in range(pages):
            url = URLs.share_url.format(new_start, self.share_every_page, uid)
            share_info = json.loads(requests.get(url, headers=headers, timeout=30).text)
            new_start += self.share_every_page
            if share_info['errno'] is not 0:
                raise LoadingError('====[ERROR]:用户分享数据加载失败')

            for s in share_info['records']:
                # note: 有些键不存在，所以需要用dict.get(),而不能使用dict[]形式
                shorturl, shareid, files = s.get('shorturl'), s.get('shareid'), s.get('filelist') if s.get('filelist') else []
                for f in files:
                    if shorturl or shareid:
                        path = file_path2.format(shorturl) if shorturl else file_path1.format(shareid, uid)
                    else:
                        continue
                    filelist.append(
                        {'title': f.get('server_filename'), 'url': path, 'size': f.get('size'), 'dir': f.get('isdir')})
        return filelist, new_start

    def _get_usr_fans(self, uid, total_fans, start, headers):
        """
        :param uid:  正在请求的用户uid
        :param headers:  http请求头
        :return: 粉丝们的uid
        note: 根据观察，当粉丝数大于2400时，最多只能获得2400个粉丝信息,这里只需要获取少了粉丝信息,因为这个响应会很慢
        """
        if total_fans == 0 or start>=total_fans:
            return [],start

        pages = self.every_pages if (total_fans-start) >= (self.every_pages*self.fans_every_page) \
            else 1+(total_fans-start)//self.fans_every_page

        fanslist, new_start = [], start
        for i in range(pages):
            url = URLs.fans_url.format(new_start, self.fans_every_page, uid)
            fans_info = json.loads(requests.get(url, headers=headers, timeout=30).text)
            new_start += self.fans_every_page
            if int(fans_info['errno']) is not 0:
                print('====[ERROR]:粉丝信息加载失败')
                return [],start
                # raise LoadingError('====[ERROR]:粉丝信息加载失败')

            fans = fans_info['fans_list'] if fans_info['fans_list'] else []  # 防止fans_list不存在，使得fans_list = None (不可迭代)
            for fan in fans:
                fanslist.append({'uid': str(fan['fans_uk']), 'total_follow': fan['follow_count'],'fans_name':fan['fans_uname'],
                                 'total_fans': fan['fans_count'], 'total_share': fan['pubshare_count']})
        return fanslist, new_start

    def _get_usr_follower(self, uid, total_follow, start, headers):
        """
        :param uid:  正在请求的用户uid
        :param follower_count:  用户的订阅数
        :param headers:  http请求头
        :return:
        """
        if total_follow == 0 or start>=total_follow:
            return [], start
        pages=self.every_pages if (total_follow - start)>=self.every_pages*self.follower_every_page \
            else 1+(total_follow - start)//self.follower_every_page

        followlist, new_start = [], start
        for i in range(pages):
            url = URLs.follow_url.format(new_start, self.follower_every_page, uid)
            follow_info = json.loads(requests.get(url, headers=headers, timeout=30).text)
            new_start += self.follower_every_page
            if int(follow_info['errno']) is not 0:
                print('    [ERROR]:获取订阅信息失败')
                return [], start
                # raise LoadingError('    [ERROR]:获取订阅信息失败')

            follows = follow_info['follow_list'] if follow_info['follow_list'] else []
            for f in follows:
                followlist.append({'uid': str(f['follow_uk']), 'total_follow': f['follow_count'],
                                   'total_fans': f['fans_count'], 'total_share': f['pubshare_count']})
        return followlist, new_start

    def get_usr_info(self, uid, start):
        """
        :param *start:用户获取信息的起始位置->（share_start, fans_start, follower_start）[元组]
        :return:
        """
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

        url = URLs.info_url.format(uid)
        try:
            infos = json.loads(requests.get(url, headers=headers, timeout=30).text)
            total_shares = infos['user_info']['pubshare_count']  # 获得分享文件数
            total_follower = infos['user_info']['follow_count']  # 获得订阅人数
            total_fans = infos['user_info']['fans_count']  # 获得粉丝人数
            # resource_weight = int(math.sqrt(int(total_fans+total_shares))) # 计算该用户资源权重

            usr_shares, share_start = self._get_usr_shares(uid, total_shares, start.share_start, headers)
            usr_fans, fans_start = self._get_usr_fans(uid, total_fans, start.fans_start, headers)
            usr_followers, follower_start = self._get_usr_follower(uid, total_follower, start.follower_start, headers)

            usr_info = USR_INFO(usr_shares, usr_fans, usr_followers)     # 构建一个命名元组对象
            new_start = START(share_start, fans_start, follower_start)
            totals = TOTAL(total_shares, total_fans, total_follower)

            self.Fail_cnt = 0  #加载成功
            return usr_info, new_start, totals
        except LoadingError as le:
            self.Fail_cnt += 1 #加载失败
            print(le)
            return [[]] * 3
        except es.ConnectionError as ce:
            self.Fail_cnt += 1  # 连接失败
            print(ce)
            return [[]]*3
        except Exception as e:
            print("==== ^_^ 网络出错了 ^_^ ====", e)
            raise

    def run(self):
        try:
            while self.total_uids < self.nums and len(self.unseen) != 0:
                uid, start = self.unseen.pop().popitem()
                if uid in self.seen:
                    continue
                if self.Fail_cnt >= Loading_Fail_Cnt:  #连续加载失败，表示ip被屏蔽，可以休眠10分钟
                    break
                print('Getting uid: \'%s\' === Total unseen uids: %d === total seen uids: %d '%(uid, len(self.unseen), len(self.seen)))

                usr_info, new_start, totals = self.get_usr_info(uid, start)

                if usr_info and (usr_info.fans or usr_info.followers or usr_info.shares):
                    [self.unseen.append({f['uid']:START(0,0,0)}) for f in usr_info.fans if f['uid'] not in self.unseen and f['total_share']]  # or f['total_follow']>20
                    [self.unseen.append({f['uid']:START(0,0,0)}) for f in usr_info.followers if f['uid'] not in self.unseen and f['total_share']]  # or f['total_fans']>20

                    if usr_info.shares:
                        db_shares.update({'uid': uid}, {'$set': {'total_share': totals.total_share}}, upsert=True)
                        db_shares.update({'uid': uid}, {'$addToSet':{'sharelist':{'$each':usr_info.shares}}}, upsert=True)
                    if usr_info.fans:
                        db_fans.update({'uid': uid}, {'$set': {'total_fans': totals.total_fans}}, upsert=True)
                        db_fans.update({'uid': uid}, {'$addToSet':{'fanslist':{'$each':usr_info.fans}}}, upsert=True)
                    if usr_info.followers:
                        db_followers.update({'uid': uid}, {'$set': {'total_follower': totals.total_follower}},upsert=True)
                        db_followers.update({'uid': uid}, {'$addToSet':{'sharelist':{'$each':usr_info.followers}}}, upsert=True)

                    if new_start.share_start >= totals.total_share:  # 如果起始文件id大于总的文件数，则表示这个用户的分享数据已经完成
                        self.total_uids += 1
                        self.seen.append(uid)
                    else:  # 否则，更新用户待爬取的文件起始id，等待下次网络连接
                        self.unseen.append({uid: new_start})

                time.sleep(self.sleep_time)
        except Exception as e:
            print('====[ERROR]:', e)
        finally:
            db_uids.update({'type':'seen'},{'$addToSet':{'uids': {'$each':list(self.seen)}}}, upsert=True)
            db.uids.update({'type':'unseen'},{'$addToSet':{'uids': {'$each':list(self.unseen)}}}, upsert=True)

    def multi_run(self):
        self.ctr_param = mp.Value('i',0)
        pool = mp.Pool(processes=5)
        pool.apply_async(self.run())

        print('任务完成，已经退出...')
        pool.close()
        pool.join()

if __name__ == '__main__':
    uids = ['697008088', '3660825403', '775105216', '154098367', '491745132']

    unseen_uids, seen_uids = deque(), deque()

    for u in next(db_uids.find({'type':'seen'},{'_id':0, 'uids':1})).get('uids'):
        seen_uids.append(u)

    for u in (next(db_uids.find({'type': 'unseen'}, {'_id': 0, 'uids': 1})).get('uids')):
        uid, start = u.popitem()
        unseen_uids.append({uid:START(*start)})

    unseen_uids = unseen_uids if len(unseen_uids) else []
    seen_uids = seen_uids if len(seen_uids) else []


    spider = BaiduYunSpider(100000,uids[4],unseen_uids,seen_uids)

    # s = spider.START(0,0,0)
    # info,*_ = spider.get_usr_info(uids[2],s)
    # [print(us) for us in info.shares if us]
    # [print(uf) for uf in info.fans if uf]
    # [print(uf) for uf in info.followers if uf]

    print('Starting Time:------------------%s----------------' % time.ctime())
    #Starting Time:------------------Thu Mar 30 00:28:25 2017----------------
    #Ending Time:-------------------Fri Apr  7 05:58:12 2017-----------------
    #Starting Time:------------------Sat Apr  8 00:36:49 2017----------------
    # Ending Time:-------------------Mon Apr 17 19:50:08 2017-----------------

    spider.run()

    print('Ending Time:-------------------%s-----------------' % time.ctime())



