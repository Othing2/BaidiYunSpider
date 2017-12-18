# coding=utf-8

from .ext import db
from datetime import datetime

__author__ = 'hanYong'


class UserLogin(db.Model):
    __tablename__ = 'sys_user_login'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    session = db.Column(db.String(64))
    user_um = db.Column(db.String(32))
    login_time = db.Column(db.DateTime, default=datetime.now)
    result = db.Column(db.String(128))


class UserInfo(db.Model):
    __tablename__ = 'sys_user_info'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_um = db.Column(db.String(32))
    user_name = db.Column(db.String(16))
    department = db.Column(db.String(128))
    first_login = db.Column(db.DateTime, default=datetime.now)
    last_login = db.Column(db.DateTime)


class UserOperation(db.Model):
    __tablename__ = 'sys_user_operations'

    id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_um = db.Column(db.String(32))
    opr_time = db.Column(db.DateTime, default=datetime.now)
    opr_type = db.Column(db.String(64))
    opr_cost = db.Column(db.Numeric(precision=11, scale=6))
    ext = db.Column(db.String(1024))


