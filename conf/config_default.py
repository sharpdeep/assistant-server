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
from datetime import datetime



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

    #上课时间对照表
    'lesson_time':{
        'duration':50, #上课时间50分钟
        '1':datetime(year=1970,month=1,day=1,hour=8,minute=0),
        '2':datetime(year=1970,month=1,day=1,hour=9,minute=0),
        '3':datetime(year=1970,month=1,day=1,hour=10,minute=10),
        '4':datetime(year=1970,month=1,day=1,hour=11,minute=10),
        '5':datetime(year=1970,month=1,day=1,hour=13,minute=0),
        '6':datetime(year=1970,month=1,day=1,hour=14,minute=0),
        '7':datetime(year=1970,month=1,day=1,hour=15,minute=0),
        '8':datetime(year=1970,month=1,day=1,hour=16,minute=10),
        '9':datetime(year=1970,month=1,day=1,hour=17,minute=10),
        '0':datetime(year=1970,month=1,day=1,hour=18,minute=10),
        'A':datetime(year=1970,month=1,day=1,hour=19,minute=10),
        'B':datetime(year=1970,month=1,day=1,hour=20,minute=10),
        'C':datetime(year=1970,month=1,day=1,hour=21,minute=10),
    },

    #错误码规律：前两位是种类，后面四位用来区分更详细的错误
    #如 签到时发生错误是10****,签到时device相关错误是100***
    'error_code':{
        'success':0,#成功
        'sign_unknow_error':100001,#未知错误
        'sign_device_error':101001,#签到device验证错误,不是本人
        'sign_day_error':102001,#签到当天没课
        'sign_time_error':102002,#签到时间错误
        'sign_room_error':103001,#签到地点错误
        'sign_identify_error':104001,#身份错误
        'sign_repeat_error':105001,#重复签到
    }
}