# coding=utf-8

from flask import Blueprint, render_template, jsonify, session, current_app, request
import json
import traceback
from ..utils import ViewDecorate
from ..apps.UserApp import UserApp
from flask_wtf import Form
from wtforms import TextField, SubmitField,StringField
from  wtforms.validators import Required

__author__ = 'hanYong'

home_view = Blueprint('home', __name__)

@home_view.route("/")
def home():
    return render_template('index.html', version=current_app.config.get('version'))

@home_view.route("/common/report.json", methods=['GET'])
@ViewDecorate.record_call_exception()
def report_default():
    beg = request.args.get('beg', 0)
    end = request.args.get('end', 0)
    time_span = request.args.get('span', 'day')
    opr_type = request.args.get('oprType')
    return jsonify(resCode=200, data=UserApp.user_operation_report(beg, end, time_span, opr_type), mess='ok')


@home_view.route("/common/report.detail.json", methods=['GET'])
@ViewDecorate.record_call_exception()
def report_detail():
    beg = request.args.get('beg', 0)
    end = request.args.get('end', 0)
    return jsonify(resCode=200, data=UserApp.user_operation_query(beg, end), mess='ok')
