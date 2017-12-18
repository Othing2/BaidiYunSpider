from collections import namedtuple


info_url = r'http://pan.baidu.com/pcloud/user/getinfo?bdstoken=null&query_uk={}&channel=chunlei&clienttype=0&web=1'
share_url = r'http://pan.baidu.com/pcloud/feed/getsharelist?category=0&auth_type=1&request_location=share_home&start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'
fans_url = r'http://pan.baidu.com/pcloud/friend/getfanslist?start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'
follow_url = 'http://pan.baidu.com/pcloud/friend/getfollowlist?start={}&limit={}&query_uk={}&channel=chunlei&clienttype=0&web=1'

URL_INFO = namedtuple('URL_INFO',['info_url','share_url','fans_url','follow_url'])
URLs = URL_INFO(info_url,share_url,fans_url,follow_url)
START = namedtuple('START', ['share_start', 'fans_start', 'follower_start'])
USR_INFO = namedtuple('USR_INFO', ['shares', 'fans', 'followers'])
TOTAL = namedtuple('TOTAL', ['total_share', 'total_fans', 'total_follower'])

Loading_Fail_Cnt = 5   #防止ip被封禁，如果连续出现5次的信息加载失败，则断开链接
SLEEP_TIME = 30