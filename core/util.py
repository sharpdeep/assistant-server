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
import logging

logger = logging.getLogger(configs.app.log.name)

login_host = 'http://credit.stu.edu.cn/portal/stulogin.aspx'
website_encoding = 'gbk'
login_timeout = 3 #seconds

def authenticate(username,passwd):
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
        '__EVENTVALIDATION': '/wEWBAKo25zdBALT8dy8BQLG8eCkDwKk07qFCRXt1F3RFYVdjuYasktKIhLnziqd' #aspx坑爹的地方

    }).encode('utf-8')

    try:
        resp = request.urlopen(login_host,postdata,login_timeout)
    except Exception as e:
        logger.error('连接学分制失败')
        return
    content = resp.read()
    if content.__contains__(b'alert'):
        logger.info('验证失败')
        return False
    else:
        logger.info('验证成功')
        return True

