# coding=utf-8

from flask import Blueprint,render_template,request,session,redirect,current_app,g,jsonify


__author__ = 'hany'


check_api = Blueprint('check', __name__)


@check_api.route("/", methods=['GET'])
def check():
    return jsonify(result='ok')