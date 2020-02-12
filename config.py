#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
    config
    -----------------------------
    配置  
    :copyright: (c) 2020 by zcyuefan.
    :license: LICENSE_NAME, see LICENSE_FILE for more details.
"""
import os
# Get the app root path
basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    # 被统计禅道用户列表，即禅道中zt_user表中的account
    ZENTAO_USERS = ['yuanxiaoju', 'majian', 'liyuan', 'liuwenli']
    # 禅道数据库设置
    ZENTAO_DB = {
        'host': '127.0.0.1',
        'port': 3306,
        'db': 'zentao',
        'user': 'root',
        'passwd': '123edcxz',
        'charset': 'utf8',
    }
    REPORTS_PATH = os.path.join(basedir, 'reports')
    TEMPLATES_PATH = os.path.join(basedir, 'templates')


default_config = Config()
