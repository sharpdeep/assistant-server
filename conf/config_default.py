#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:config_default.py
@time: 2016-01-01 21:39
"""

import logging
import os
from uuid import uuid4



configs = {
    'app':{
        'debug':True,
        'host':'0.0.0.0',
        'port':5000,
        'log':{
            'name':'main',
            'logLevel':logging.INFO,
            'logFile':os.path.abspath('./log/main.log'),
            'maxBytes':5*1024*1024,
            'backupCount':50,
        },
        'jwt_secret':'',
        'exprire':7*24*3600,#一个星期
    },

    'db':{
        'host':'127.0.0.1',
        'port':3306,
        'username':'',
        'password':'',
        'name':'assistant',
    },
}