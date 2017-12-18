# coding=utf-8

from ...rawFlask.ext import db
from ...rawFlask.models import UserInfo, UserLogin, UserOperation
from datetime import datetime, timedelta
from flask import current_app
import time

__author__ = 'hanYong'

TIME_SPAN = {
    'day': 3600 * 24,
    'hour': 3600
}

TIME_LABEL = {
    'day': '%Y/%m/%d',
    'hour': '%Y/%m/%d %H%M'
}


class UserApp(object):
    @classmethod
    def users(cls):
        ret_list = list()
        for item in db.session.query(UserInfo).all():
            ret_list.append({'user': item.user_name, 'um': item.user_um})
        return ret_list

    @classmethod
    def login(cls, um, session, info):
        tmp = UserLogin(user_um=um, session=session, result=info)
        db.session.add(tmp)
        db.session.commit()
        return tmp.id

    @classmethod
    def sync_user(cls, um, name, department):
        cnt = db.session.query(UserInfo).filter(UserInfo.user_um == um).first()
        if cnt:
            db.session.query(UserInfo).filter(UserInfo.user_um == um).update({
                UserInfo.user_name: name, UserInfo.department: department, UserInfo.last_login: datetime.now()
            })
        else:
            tmp = UserInfo(user_um=um, user_name=name, department=department)
            db.session.add(tmp)
        db.session.commit()
        return 1

    @classmethod
    def user_operation_add(cls, um, opr_type, ext, force=False):
        if len(str(ext)) > 1020:
            current_app.logger.warning('UserApp.user_operation_add ext too long : %s', ext)
            if force:
                ext = ext[0: 1020]
        tmp = UserOperation(um, opr_type, ext)
        db.session.add(tmp)
        db.session.commit()
        return tmp.id

    @classmethod
    def user_operation_query(cls, beg_int, end_int):
        ret_list = list()
        try:
            beg_str = time.strftime('%Y%m%d%H%M', time.localtime(int(beg_int)/1000))
            end_str = time.strftime('%Y%m%d%H%M', time.localtime(int(end_int)/1000))
            beg_time = datetime.strptime(beg_str, '%Y%m%d%H%M')
            end_time = datetime.strptime(end_str, '%Y%m%d%H%M')
        except:
            return ret_list

        print('>>>>', beg_time, end_time)
        for item in db.session.query(UserOperation).filter(UserOperation.opr_time.between(beg_time, end_time)).all():
            ret_list.append({
                'id': item.id, 'um': item.user_um, 'oprType': item.opr_type,
                'oprTime': item.opr_time.strftime('%Y/%m/%d %H:%M:%S'), 'ext': item.ext, 'costTime': str(item.opr_cost)
            })
        return ret_list

    @classmethod
    def user_operation_report(cls, beg_int, end_int, time_span, opr_type):
        ret_report = {
            'time_report': [],
            'user_report': []
        }

        time_span_delta = TIME_SPAN.get(time_span.lower(), 3600 * 24)
        time_label = TIME_LABEL.get(time_span.lower(), '%Y/%m/%d')

        beg_int_real = int(int(beg_int)/1000/time_span_delta) * time_span_delta
        real_cnt = int((int(end_int) - int(beg_int))/1000/time_span_delta) + 1

        user_dict = dict()

        for i in range(real_cnt):
            beg_int_t = beg_int_real + i * time_span_delta
            end_int_t = beg_int_real + (i + 1) * time_span_delta
            ret_list = cls.user_operation_query(beg_int_t * 1000, end_int_t * 1000)
            time_content = {
                'time': time.strftime(time_label, time.localtime(beg_int_t)),
                'cnt': 0
            }
            for ret in ret_list:
                ret_um = ret.get('um')
                if user_dict.keys().count(ret_um) == 0:
                    user_dict[ret_um] = 0
                if ret.get('oprType') == opr_type:
                    time_content['cnt'] += 1
                    user_dict[ret_um] += 1
            ret_report['time_report'].append(time_content)
        for usr, o_cnt in user_dict.items():
            ret_report['user_report'].insert(0, {'usr': usr, 'cnt': o_cnt})

        return ret_report



