# coding=utf-8

from flask import Blueprint, render_template, jsonify, session, current_app, request, redirect, url_for, g
# from urllib import quote
import json
import traceback
from ..utils import ViewDecorate
from ..auth import Auth
from ..apps.UserApp import UserApp
import requests

__author__ = 'hanYong'

account = Blueprint('account', __name__)


class JSON_CODE(object):
    OK = 200
    PasswordError = 405
    Unauthorized = 401
    Forbidden = 403
    ServerError = 500
    RemoteError = 505


@account.route("/logout.json", methods=['GET'])
@ViewDecorate.record_call_exception()
def logout_raw():
    if session.get('user_token'):
        token = session.pop("user_token")
        um_id = session.pop("id")
        um = session.pop("um")
    return jsonify({'resCode': 200, 'data': 'ok'})


@account.route("/login.status.check.json", methods=['GET'])
@ViewDecorate.record_call_exception()
def login_status_check():
    if session.get('user_token') is not None:
        Auth.load_user()
        if g.user.get('permissions', list()).count('super.admin') > 0:
            g.user['isAdmin'] = True
        else:
            g.user['isAdmin'] = False
        return jsonify({'resCode': 200, 'data': g.user})
    else:
        return jsonify({'resCode': 404, 'data': {}})


@account.route("/users.list.json", methods=['GET'])
@ViewDecorate.record_call_exception()
def users_list():
    return jsonify({'resCode': 200, 'data': UserApp.users()})


@account.route("/login.json", methods=["POST"])
@ViewDecorate.record_call_exception()
def login_sso():
    user = request.get_json().get("user")
    um_id = None
    um = None
    data = None
    message = "successful"
    code = JSON_CODE.OK
    success = True
    appid = current_app.config.get("SSO_APP_ID")
    is_test_mode = current_app.config.get("IS_TEST")
    if current_app.debug:
        login_type = "local"
    else:
        login_type = "oa"
    try:
        req = requests.post("%s/%s" % (current_app.config.get("SSO_URL"), "account/api_login.json"), {
            "um": user["um"],
            "password": user["password"],
            "login_type": login_type,
            "is_debug": is_test_mode,
            "appid": appid
        })
        if req.status_code == 200:
            resp = req.json()
            code = resp["code"]
            if code == 200 and resp["success"]:
                session["user_token"] = resp["data"]
                url = '%s/account/user_info.json?token=%s&secret=%s&app=%d' % (
                    current_app.config.get('SSO_URL'),
                    session["user_token"],
                    current_app.config.get('SSO_APP_SECRET'),
                    current_app.config.get('SSO_APP_ID')
                )
                req = requests.get(url)
                resp = req.json()
                if resp['code'] == 200 and resp["success"]:
                    g.user = resp["data"]

                    if 'super.super' in g.user['permissions']:
                        session['is_super'] = 1
                    else:
                        session['is_super'] = 0

                    if 'login.login' in g.user['permissions'] or 'super.admin' in g.user['permissions']:
                        session['id'] = g.user['id']
                        session['um'] = g.user['um']
                        message = "successful"
                        current_app.logger.info('user login success ~> um %s token: %s' %
                                                (user['um'], session["user_token"]))
                        UserApp.login(user['um'], session["user_token"], JSON_CODE.OK)
                        if len(g.user.get('department', list())) > 0:
                            department = g.user['department'][0]
                        else:
                            department = ''
                        UserApp.sync_user(user['um'], g.user['name'], department)
                        code = JSON_CODE.OK
                        success = True
                        data = 0
                    else:
                        success = False
                        message = u'没有登录权限'
                        current_app.logger.info('user login fail ~> um %s token: %s message %s' %
                                                (user['um'], session["user_token"], u'没有登录权限'))
                        UserApp.login(user['um'], session["user_token"], JSON_CODE.Unauthorized)
                else:
                    current_app.logger.info('user login fail ~> um %s message %s' %
                                                    (user['um'], u'Passport出现未知错误'))
                    message = u"Passport出现未知错误"
                    UserApp.login(user['um'], '', JSON_CODE.RemoteError)
                    success = False
            else:
                current_app.logger.info('user login fail ~> um %s message %s' %
                                           (user['um'], resp["message"]))
                UserApp.login(user['um'], '', JSON_CODE.PasswordError)
                message = resp["message"]
                success = False
        else:
            current_app.logger.info('user login fail ~> um %s message %s' %
                                    (user['um'], u"验证失败，请检查密码是否正确"))
            UserApp.login(user['um'], '', JSON_CODE.PasswordError)
            message = u"验证失败，请检查密码是否正确"
            success = False
    except Exception as err:
        message = err.message
        success = False
        code = JSON_CODE.ServerError
        UserApp.login(user['um'], '', JSON_CODE.ServerError)
        current_app.logger.warning('user login fail internal error ~> %s' % traceback.format_exc()+'\n'+str(err))
    return jsonify({"code": code, "um_id": um_id, "um": um, "data": data, "message": message, "success": success})



