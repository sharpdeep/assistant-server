#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:util.py
@time: 2016-01-02 00:19
"""
from urllib import parse
from urllib import request
from conf.config import configs
from http import cookiejar
from core.state import *
import logging

logger = logging.getLogger(configs.app.log.name)

login_host = 'http://credit.stu.edu.cn/portal/stulogin.aspx'
website_encoding = 'gbk'
login_timeout = 3 #seconds

def authenticate(username,passwd,login=False):
    """
    利用学分制验证用户
    :param username:
    :param passwd:
    :return:True->验证成功，False->验证失败，None->error
    """
    postdata = parse.urlencode({
        "txtUserID": username,
        "txtUserPwd": passwd,
        "btnLogon": "登录",
        '__VIEWSTATE': '/wEPDwUKMTM1MzI1Njg5N2Rk47x7/EAaT/4MwkLGxreXh8mHHxA=',
        '__EVENTVALIDATION': '/wEWBAKo25zdBALT8dy8BQLG8eCkDwKk07qFCRXt1F3RFYVdjuYasktKIhLnziqd', #aspx坑爹的地方
    }).encode('utf-8')

    if login:
        cookie_jar = cookiejar.CookieJar()
        opener = request.build_opener(request.HTTPCookieProcessor(cookie_jar))
        try:
            resp = opener.open(login_host,postdata,login_timeout)
        except Exception as e:
            print(e)
            return error(Error.CONNECT_ERROR)
        content = resp.read()
        if content.__contains__(b'alert'):
            return failed('验证失败')
        else:
            return success('登陆成功',data={'opener':opener})
    else:
        try:
            resp = request.urlopen(login_host,postdata,login_timeout)
        except Exception as e:
            return error(Error.CONNECT_ERROR)
        content = resp.read()
        if content.__contains__(b'alert'):
            return failed('验证失败')
        else:
            return success('验证成功')



