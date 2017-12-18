# coding=utf-8

from flask.ext.sqlalchemy import SQLAlchemy
from flask_redis import Redis

__author__ = 'hany'


db = SQLAlchemy()
cache = Redis()
