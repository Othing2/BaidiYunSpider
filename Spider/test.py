from pymongo import *
from collections import deque
import re

client = MongoClient()
db = client.BaiduYunPan           #数据库
db_shares = db.shares     #分享数据表单
db_followers = db.followers   #订阅表单
db_fans = db.fans         #粉丝表单
db_uids = db.uids



##------查询数据-----##
query = [r'速度与激情']

for i in range(len(query)-1,-1,-1):
    query.insert(i,r'.*')
search = ''.join(query)

shares = db_shares.find({},{'_id': 0, 'sharelist':1})
[ print(v) for s in shares for v in s.get('sharelist') if re.match(search, v.get('title'), flags=re.IGNORECASE) ]

##------查询单个用户-------##
# for s in db_shares.find({'uid':'2340839038'}):
#     print(s)
#     p = s.get('sharelist')
#     print(len(p))

# shares_one = db_shares.find_one()
# [print(k,v) for k,v in shares_one.items()]

##----统计分享数据------##
# total_file, total_user = 0, 0
# for doc in db_shares.find():
#     share = doc.get('sharelist')
#     total_file += len(share)
#     total_user += 1
# print('total user:',total_user)
# print('total file:',total_file)

##------统计用户ID------##
# for doc in db.uids.find({'type':'seen'}):
#     seen_uids = doc.get('uids')
#     print('seen uids:',len(seen_uids))
#
# for doc in db.uids.find({'type':'unseen'}):
#     unseen_uids = doc.get('uids')
#     print('unseen uids',len(unseen_uids))








