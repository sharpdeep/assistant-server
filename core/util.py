#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:util.py
@time: 2016-01-02 00:19
"""
from conf.config import configs
from core.status import *
from datetime import datetime
from enum import Enum,unique
import requests
import logging

logger = logging.getLogger(configs.app.log.name)

login_host = 'http://credit.stu.edu.cn/portal/stulogin.aspx'
website_encoding = 'gbk'
login_timeout = 3 #seconds

@unique
class semester(Enum):
    AUTUMN = 0
    SPRING = 1
    SUMMER = 2

def authenticate(username,passwd,login=False):
    postdata = {
        "txtUserID": username,
        "txtUserPwd": passwd,
        "btnLogon": "登录",
        '__VIEWSTATE': '/wEPDwUKMTM1MzI1Njg5N2Rk47x7/EAaT/4MwkLGxreXh8mHHxA=',
        '__EVENTVALIDATION': '/wEWBAKo25zdBALT8dy8BQLG8eCkDwKk07qFCRXt1F3RFYVdjuYasktKIhLnziqd', #aspx坑爹的地方
    }
    try:
        resp = requests.post(login_host,postdata,login_timeout)
    except Exception as e:
        return error(Error.CONNECT_ERROR)
    if resp.content.__contains__(b'alert'):
        return failed('验证失败')
    if not login:
        return success('验证成功')
    return success('登陆成功',data={'cookie':resp.cookies})

