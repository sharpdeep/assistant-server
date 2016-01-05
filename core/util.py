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
from urllib import request,parse
from http import cookiejar
from enum import Enum,unique
import requests
import logging

logger = logging.getLogger(configs.app.log.name)

website_encoding = 'gbk'
default_timeout = 3 #seconds

login_host = 'http://credit.stu.edu.cn/portal/stulogin.aspx'
schedule_host = 'http://credit.stu.edu.cn/Elective/MyCurriculumSchedule.aspx'
curriculum_base_url = b'http://credit.stu.edu.cn/Student/StudentTimeTable.aspx?'

@unique
class Semester(Enum):
    AUTUMN = 1
    SPRING = 2
    SUMMER = 3

def authenticate(username,passwd,login=False):
    postdata = parse.urlencode({
        "txtUserID": username,
        "txtUserPwd": passwd,
        "btnLogon": "登录",
        '__VIEWSTATE': '/wEPDwUKMTM1MzI1Njg5N2Rk47x7/EAaT/4MwkLGxreXh8mHHxA=',
        '__EVENTVALIDATION': '/wEWBAKo25zdBALT8dy8BQLG8eCkDwKk07qFCRXt1F3RFYVdjuYasktKIhLnziqd', #aspx坑爹的地方
    }).encode('utf-8')

    if not login:
        try:
            resp = request.urlopen(login_host,postdata,timeout=default_timeout)
        except Exception as e:
            return error(Error.CONNECT_ERROR)
        if resp.read().__contains__(b'alert'):
            return failed('验证失败')
        else:
            return success('验证成功')
    else:
        cookie_jar = cookiejar.CookieJar()
        opener = request.build_opener(request.HTTPCookieProcessor(cookie_jar))
        resp = opener.open(login_host,postdata,default_timeout)
        if resp.read().__contains__(b'alert'):
            return failed('验证失败')
        else:
            return success('登陆成功',data={'opener':opener})


def get_syllabus(username,passwd,start_year=datetime.now().year,semester=Semester.AUTUMN):
    ret_val = authenticate(username,passwd,login=True)
    if not ret_val.status == Status.SUCCESS:
        return ret_val
    try:
        opener = ret_val.data.opener
        #得到学号和lock参数
        resp = opener.open(schedule_host, timeout=default_timeout)
        content = resp.read()
        start_str = b'.aspx?'
        start_index = content.find(start_str)
        end_index = content.find(b' ', start_index)
        args = content[start_index + len(start_str): end_index - 1]

        #拼接url
        curriculum_url = (curriculum_base_url+args).decode(website_encoding)

        data = gen_syllabus_post_data(start_year,semester)
        resp = opener.open(curriculum_url,data=data,timeout=default_timeout)
    except Exception as e:
        print(e)
        return error(Error.CONNECT_ERROR)
    content = resp.read()
    return success(data={'content':content.decode('gbk').encode('utf-8')})


def gen_syllabus_post_data(start_year=datetime.now().year,semester=Semester.AUTUMN):
    data =('__EVENTTARGET=&__EVENTARGUMENT=' \
              '&__VIEWSTATE=%2FwEPDwUKLTc4MzA3NjE3Mg9kFgICAQ9kFgYCAQ9kFgRmDxAPFgIeBFRleHQFDzIwMTUtMjAxNuWtpuW5tGQQFQcPMjAxMi0yMDEz5a2m5bm0DzIwMTMtMjAxNOWtpuW5tA8yMDE0LTIwMTXlrablubQPMjAxNS0yMDE25a2m5bm0DzIwMTYtMjAxN%2BWtpuW5tA8yMDE3LTIwMTjlrablubQPMjAxOC0yMDE55a2m5bm0FQc' \
              'PMjAxMi0yMDEz5a2m5bm0DzIwMTMtMjAxNOWtpuW5tA8yMDE0LTIwMTXlrablubQPMjAxNS0yMDE25a2m' \
              '5bm0DzIwMTYtMjAxN%2BWtpuW5tA8yMDE3LTIwMTjlrablubQPMjAxOC0yMDE55a2m' \
              '5bm0FCsDB2dnZ2dnZ2cWAGQCAQ8QZGQWAQICZAIFDxQrAAsP' \
              'FggeCERhdGFLZXlzFgAeC18hSXRlbUNvdW50Zh4JUGFnZUNvdW50Ag' \
              'EeFV8hRGF0YVNvdXJjZUl0ZW1Db3VudGZkZBYEHghDc3NDbGFzcwUMREdQYWdlclN0eWxlHgRfIVN' \
              'CAgIWBB8FBQ1ER0hlYWRlclN0eWxlHwYCAhYEHwUFDURHRm9vdGVyU3R5bGUfBgICFgQfBQULREdJdGVtU3R5bGUfBgICFgQfBQUWREdBbHRlcm5hdGluZ0l0ZW1TdHlsZR8GAgIWBB8FBRNER1NlbGVjdGVkSXRlbVN0eWxlHwYCAhYEHwUFD0RHRWRpdEl0ZW1TdHlsZR8GAgIWBB8FBQJERx8GAgJkFgJmD2QWAgIBD2QWBAIDDw8WAh8ABQ3lhbEw6Zeo6K' \
              '%2B%2B56iLZGQCBA8PFgIfAAUHMOWtpuWIhmRkAgYPFCsACw8WAh4HVmlzaWJsZWhkZBYEHwUFDERHUGFnZXJTdHlsZR8GAgIWBB8FBQ1ER0hlYWRlclN0eWxlHwYCAhYEHwUFDURHRm9vdGVyU3R5bGUfBgICFgQfBQULREdJdGVtU3R5bGUfBgICFgQfBQUWREdBbHRlcm5hdGluZ0l0ZW1TdHlsZR8GAgIWBB8FBRNER1NlbGVjdGVkSXRlbVN0eWxlHwYCAhYEHwUFD0RHRWRpdEl0ZW1TdHlsZR8GAgIWBB8FBQJERx8GAgJkZBgBBR5fX0NvbnRyb2xzUmVxdWlyZVBvc3RCYWNrS2V5X18WAgUIdWNzWVMkWE4FCWJ0blNlYXJjaIOA1hvkaeyr6hBNdPilFTCCDv8u' \
              '&__VIEWSTATEGENERATOR=E672B8C6&__EVENTVALIDATION=%2FwEWDgKP7Z%2FyDQKA2K7WDwKl3bLICQKs3faYCwKj3ZrWCALF5PiNDALE5IzLDQLD5MCbDwKv3YqZDQL7tY9IAvi1j0gC' \
              '%2BrWPSAL63YQMAqWf8%2B4KZKbR9XsGkypHcOunFkHTcdqR6to%3D&' \
              'ucsYS%24XN%24Text={}-{}%' \
              'D1%A7%C4%EA&ucsYS%24XQ=' + str(semester) + '&ucsYS%24hfXN=&btnSearch.x=42&btnSearch.y=21').format(start_year, start_year+1)

    return data.encode('utf-8')
