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
from bs4 import BeautifulSoup
from core.model import Lesson
import logging

logger = logging.getLogger(configs.app.log.name)

website_encoding = 'gbk'
default_timeout = 3 #seconds

login_host = 'http://credit.stu.edu.cn/portal/stulogin.aspx'
schedule_host = 'http://credit.stu.edu.cn/Elective/MyCurriculumSchedule.aspx'
curriculum_base_url = b'http://credit.stu.edu.cn/Student/StudentTimeTable.aspx?'
student_info_url = 'http://credit.stu.edu.cn/Student/DisplayStudentInfo.aspx'

@unique
class Semester(Enum):
    AUTUMN = 1
    SPRING = 2
    SUMMER = 3

def authenticate(username,passwd,login=False):
    """
    验证用户，当login为True,返回值中ret_val.data.opener为一个opener
    :param username:
    :param passwd:
    :param login:
    :return:
    """
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


def get_syllabus_page(username,passwd,start_year=datetime.now().year,semester=Semester.AUTUMN.value):
    """
    获取课表页面
    :param username:
    :param passwd:
    :param start_year:
    :param semester:
    :return:
    """
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
        return error(Error.CONNECT_ERROR)
    content = resp.read()
    return success(data={'content':content.decode('gbk')})

def get_student_info_page(username,passswd):
    ret_val = authenticate(username,passswd,login=True)
    if not ret_val.status == Status.SUCCESS:
        return ret_val
    opener = ret_val.data.opener
    try:
        resp = opener.open(student_info_url)
    except Exception as e:
        return error(Error.CONNECT_ERROR)

    content = resp.read().decode(website_encoding)
    return success(data={'content':content})

class SyllabusParser(object):
    """
    传入一个完整的课表页面字符串，输出课程。
    usage：
    parser = SyllabusParser(content)
    lessons = parser.parse()
    lessons是lesson对象的列表
    """
    def __init__(self,content):
        self.content = content

    def __getSyllabusTableStr(self):
        start_index = self.content.find('<tr class="DGItemStyle')
        end_index = self.content.find('<tr class="DGFooterStyle">')
        return self.content[start_index:end_index]

    def parse(self):
        syllabusSoup = BeautifulSoup(self.__getSyllabusTableStr(),'html.parser')
        lessons = [[item.text.strip() for item in lesson.find_all('td')] for lesson in syllabusSoup.find_all('tr')]

        return lessons

class StudentInfoParser(object):
    def __init__(self,content):
        self.content = content

    def parse(self):
        def text(span_id):
            return soup.find('span',id=span_id).text.strip()
        info = dict()

        soup = BeautifulSoup(self.content,'html.parser')
        info['name'] = text('Label1')
        info['vid'] = text('Label3')
        info['address'] = text('Label4')
        info['studen_id'] = text('Label5')
        info['gender'] = text('Label7')
        info['birthday'] = text('Label8')
        info['identify_id'] = text('Label9')
        info['nation'] = text('Label10')
        info['college'] = text('Label11')
        info['major'] = text('Label12')
        info['grade'] = text('Label13')
        info['enrolmentdate'] = text('Label14') #入学时间
        info['tutor'] = text('Label15')
        info['status'] = text('Label16') #学期状态
        info['nativeplace'] = text('Label17') #籍贯
        info['familyphone'] = text('Label18')
        info['postalcode'] = text('Label19')

        return info


def gen_syllabus_post_data(start_year=datetime.now().year,semester=Semester.AUTUMN.value):
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
