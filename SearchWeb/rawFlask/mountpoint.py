# coding=utf-8

from .apis.check import check_api
from .views.index import home_view
from .views.account import account
from .views.result import result


__author__ = 'hany'


MOUNT_POINTS = (
    (check_api, '/s/check'),
    (home_view, '/s'),
    (home_view, '/'),
    (result,'/qr'),
    (account, '/s/account'),
)