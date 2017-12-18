# coding=utf-8

__author__ = 'comyn'


class Config(object):
    APP_NAME = 'BaiduYun'  # change to usr app name
    DEBUG = True
    SECRET_KEY = 'sddfdsjksdghkdsjfk'
    CSRF_ENABLED = True

    BABEL_DEFAULT_LOCALE = 'zh_CN'
    ACCEPT_LANGUAGES = ['en', 'zh']

    APPLICATION_ROOT = "/Web"  # change to user own root

    STATIC_URL_PATH = "/Web/static"  # change to user own static path
    STATIC_FOLDER = "static"

    LOG_PATH = './logs'
    version = '1.0.0'


class ProductionConfig(Config):
    DEBUG = False

    LOG_LEVEL = 'INFO'

    SQLALCHEMY_DATABASE_URI = 'mysql://root:12qwaszx@127.0.0.1:3306/rawFlask?charset=utf8'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 300


class DevelopmentConfig(Config):
    DEBUG = True

    LOG_LEVEL = 'DEBUG'

    # define database connection
    SQLALCHEMY_DATABASE_URI = 'mysql://root:12qwaszx@127.0.0.1:3306/rawFlask?charset=utf8'
    SQLALCHEMY_ECHO = False
    SQLALCHEMY_POOL_SIZE = 10
    SQLALCHEMY_POOL_RECYCLE = 300

    # define redis if needed
    REDIS_URL = "redis://127.0.0.1:6379/1"

    # define sso configure
    SSO_URL = 'http://172.19.46.26:8000/passport'
    SSO_APP_SECRET = 'ZhfEZBd64GJX6X5H'
    SSO_APP_ID = 9
    SSO_ENABLE = True
    IS_TEST = True

    LOCAL_USER = {

    }  # local user used while SSO_ENABLE is set to False ,
    # local_user should be the callback data from passport as example

    






