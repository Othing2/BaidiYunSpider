# -*- coding:utf8 -*-
from flask import Blueprint, render_template, jsonify, session, current_app, request

from flask_wtf import Form
from wtforms import StringField,SubmitField
from wtforms.validators import Required

from pymongo import *
import re

client = MongoClient()
db = client.BaiduYunPan           #数据库
db_shares = db.shares     #分享数据表单
db_followers = db.followers   #订阅表单
db_fans = db.fans         #粉丝表单
db_uids = db.uids

__auth__="Hugg"

result = Blueprint('Result',__name__)

class QueryForm(Form):
    query = StringField('query')
    submit = SubmitField('stb')

@result.route('/result.json',methods=['GET','POST'])
def query_result():
    rs = []
    form = QueryForm()
    query = form.query.data
    qw = re.split(" +",query.strip())

    for i in range(len(qw) - 1, -1, -1):
        qw.insert(i, r'.*')
    search = ''.join(qw)
    shares = db_shares.find({}, {'_id': 0, 'sharelist': 1})
    [rs.append(v) for s in shares for v in s.get('sharelist') if re.match(search, v.get('title'), flags=re.IGNORECASE)]

    return render_template("result.html", Query=query,
                                             ResultSet=rs)