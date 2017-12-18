# coding=utf-8

import sys
import logging
from logging import StreamHandler
from logging.handlers import SMTPHandler
from flask import Flask, request
# from flask.ext.babel import Babel
# from flask.ext import breadcrumbs
from .ext import db, cache
import os
from logging.handlers import RotatingFileHandler

__author__ = 'hany'


def create_app(conf=None):
    app = Flask(conf.APP_NAME,
                static_url_path=conf.STATIC_URL_PATH,
                static_folder=conf.STATIC_FOLDER
                )
    if conf:
        app.config.from_object(conf)
    configure_extensions(app)
    configure_logging(app)
    return app


def configure_extensions(app):
    db.app = app
    db.init_app(app)
    cache.init_app(app)


def configure_blueprints(app, modules):
    for module, url_prefix in modules:
        app.register_blueprint(module, url_prefix=url_prefix)
    return app


def configure_logging(app):
    formatter = logging.Formatter("%(asctime)s %(levelname)s %(process)s %(pathname)s %(lineno)d - %(message)s")

    rotate_handler = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'firefly.log'), maxBytes=20*1024*1024,
                                         backupCount=10)
    rotate_handler.setFormatter(formatter)
    rotate_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))

    console_handler = StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    console_handler.setLevel(getattr(logging, app.config.get('LOG_LEVEL', 'INFO')))
    app.logger.addHandler(console_handler)
    app.logger.addHandler(rotate_handler)
    app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))

    rotate_handler_db = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'db.log'), maxBytes=20*1024*1024,
                                            backupCount=5)
    rotate_handler_db.setFormatter(formatter)
    rotate_handler_db.setLevel(app.config['LOG_LEVEL'])

    rotate_handler_int = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'inter.log'), maxBytes=20*1024*1024,
                                             backupCount=5)
    rotate_handler_int.setFormatter(formatter)
    rotate_handler_int.setLevel(app.config['LOG_LEVEL'])

    rotate_handler_app = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'app.log'), maxBytes=20*1024*1024,
                                             backupCount=5)
    rotate_handler_app.setFormatter(formatter)
    rotate_handler_app.setLevel(app.config['LOG_LEVEL'])

    rotate_handler_access = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'view.log'), maxBytes=20*1024*1024,
                                                backupCount=5)
    rotate_handler_access.setFormatter(formatter)
    rotate_handler_access.setLevel(app.config['LOG_LEVEL'])

    rotate_handler_mod = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'mod.log'), maxBytes=20*1024*1024,
                                             backupCount=5)
    rotate_handler_mod.setFormatter(formatter)
    rotate_handler_mod.setLevel(app.config['LOG_LEVEL'])

    rotate_handler_login = RotatingFileHandler(os.path.join(app.config['LOG_PATH'], 'login.log'), maxBytes=20*1024*1024,
                                               backupCount=5)
    rotate_handler_login.setFormatter(formatter)
    rotate_handler_login.setLevel(app.config['LOG_LEVEL'])

    logger = logging.getLogger('log_view')
    logger_db = logging.getLogger('log_db')
    logger_int = logging.getLogger('log_int')
    logger_app = logging.getLogger('log_app')
    logger_mod = logging.getLogger('log_mod')
    logger_login = logging.getLogger('log_login')

    logger.addHandler(rotate_handler_access)
    logger.addHandler(console_handler)
    logger.setLevel(app.config['LOG_LEVEL'])

    logger_db.addHandler(rotate_handler_db)
    logger_db.addHandler(console_handler)
    logger_db.setLevel(app.config['LOG_LEVEL'])

    logger_int.addHandler(rotate_handler_int)
    logger_int.addHandler(console_handler)
    logger_int.setLevel(app.config['LOG_LEVEL'])

    logger_app.addHandler(rotate_handler_app)
    logger_app.addHandler(console_handler)
    logger_app.setLevel(app.config['LOG_LEVEL'])

    logger_mod.addHandler(rotate_handler_mod)
    logger_mod.addHandler(console_handler)
    logger_mod.setLevel(app.config['LOG_LEVEL'])

    logger_login.addHandler(rotate_handler_login)
    logger_login.setLevel(app.config['LOG_LEVEL'])
