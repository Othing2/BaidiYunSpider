# coding=utf-8

from datetime import datetime
import logging
import traceback
from flask import jsonify
from functools import wraps

__author__ = 'hany'


view_logger = logging.getLogger('log_view')
long_logger = logging.getLogger('long-exe')


class ViewDecorate(object):

    @classmethod
    def record_view_exception(cls):
        def wrap(func):
            @wraps(func)
            def record_exception(*args, **kwargs):
                beg_time = datetime.now()
                try:
                    back = func(*args, **kwargs)
                    end_time = datetime.now()
                    time_dtt = str((end_time - beg_time).total_seconds())
                    view_logger.info('func: %s, cost:%s s' % (func.__name__, time_dtt))
                    return back
                except Exception as e:
                    end_time = datetime.now()
                    time_dtt = str((end_time - beg_time).total_seconds())
                    view_logger.warning('func: %s, cost:%s s, error:%s' % (func.__name__, time_dtt,
                                                                           traceback.format_exc()+'\n'+str(e)))
                    return 'Internal Error'
            return record_exception
        return wrap

    @classmethod
    def record_call_exception(cls):
        def wrap(func):
            @wraps(func)
            def record_exception(*args, **kwargs):
                beg_time = datetime.now()
                try:
                    back = func(*args, **kwargs)
                    end_time = datetime.now()
                    time_dtt = str((end_time - beg_time).total_seconds())
                    view_logger.info('func: %s, cost:%s s' % (func.__name__, time_dtt))
                    if float(time_dtt) > 5.0:
                        long_logger.info('func: %s, cost: %s s detail: %s, %s' % (func.__name__, time_dtt, args, kwargs))
                    return back
                except Exception as e:
                    end_time = datetime.now()
                    time_dtt = str((end_time - beg_time).total_seconds())
                    view_logger.warning('func: %s, cost:%s s, error:%s' % (func.__name__, time_dtt,
                                                                           traceback.format_exc()+'\n'+str(e)))
                    if float(time_dtt) > 5.0:
                        long_logger.warning('func: %s, cost: %s s detail: %s, %s error: %s' %
                                            (func.__name__, time_dtt, args, kwargs, traceback.format_exc()+'\n'+str(e)))
                    return jsonify({'resCode': 500, 'data': None, 'mess': traceback.format_exc()+'\n'+str(e)})
            return record_exception
        return wrap

