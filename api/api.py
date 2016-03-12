#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:api.py
@time: 2016-01-01 19:59

RESTful API 处理模块

"""

from flask import Blueprint,request
from flask.ext.restful import Resource,Api,reqparse
from app import app
import functools
from enum import Enum,unique
from core.model import *
from core.status import *
from core import util

@unique
class Identify(Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'

api = Api(app)
api_prefix = '/api'

def api_route(*urls,**kwargs):
    """
    装饰器,将Resources类与url关联起来,并添加前缀
    :param urls:一个或多个path,path不能为'/api'?
    :param kwargs:
    :return:
    """
    def decorator(cls):
        @functools.wraps(cls)
        def wrapper(*args,**kw):
            return cls(*args,**kw)
        #参数检查
        if len(urls) < 1:
            raise ValueError('no url in urls for Resource:%s'%cls.__name__)
        #添加前缀
        prefix_urls = list(urls)
        for i in range(len(prefix_urls)):
            prefix_urls[i] = api_prefix+prefix_urls[i]
        api.add_resource(cls,*prefix_urls,**kwargs)
        return wrapper
    return decorator

def add_args(parser,*arguments):
    """
    装饰器，方便post和put等参数解析
    :param parser:
    :param arguments:
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            return func(*args,**kwargs)
        for arg in arguments:
            if not isinstance(arg,tuple):
                raise ValueError('arg in arguments should be tuple')
            arg_list = list()
            kw = dict()
            for i in arg:
                if isinstance(i,dict):
                    kw = i
                else:
                    arg_list.append(i)
            parser.add_argument(*arg_list,**kw)
        return wrapper
    return decorator

def token_check(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        token = request.headers['Authorization']
        # print(token)
        payload = util.parser_token(token)
        print('['+payload.identify+']'+payload.username+' auth in '+str(datetime.fromtimestamp(payload.timestamp)))
        nowtime = int(datetime.now().timestamp())
        if not payload:
            return syllabus_result(failed,'illegal token')
        if nowtime - payload.timestamp > configs.app.exprire:
            return syllabus_result(failed,'exprire token')
        else:
            return func(*args,**kwargs)
    return wrapper

@api_route('/auth')
class AuthResource(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('username',str),('password',str))
    def post(self):
        args = self.parser.parse_args()
        username = args['username']
        password = args['password']

        teacher = Teacher.objects(account=username,password=password).first()
        if teacher: #判断为教师账号
            token = util.gen_token(username,Identify.TEACHER.value)
            teacher.token = token #更新token
            teacher.save()
            return auth_result(success,'auth teacher from database',token,Identify.TEACHER.value)

        # #不在教师数据库中，那么就可能是学生账号或非法账号
        token = util.gen_token(username,Identify.STUDENT.value)
        ret_val = util.authenticate(username,password)
        if ret_val.status == Status.SUCCESS.value: #验证成功，缓存info到数据库
            ret_val = util.get_student_info_page(username,password)
            if ret_val.status == Status.SUCCESS.value:
                parser = util.StudentInfoParser(ret_val.content)
                ret_val = parser.parse()
                student = Student.update_or_create(account=username,password=password,token=token)
                student.save_from_dict(ret_val.info) #顺便存储学生信息
                return auth_result(success,'auth from credit',token,Identify.STUDENT.value)
            else:
                return auth_result(failed,'failed to get student info')
        else:
                return auth_result(failed,'failed to login credit')

def auth_result(status_func,msg='',token='',identify=''):
    return status_func(msg,data={'token':token,'identify':identify})

@api_route('/syllabus/<string:start_year>/<int:semester>')
class SyllabusResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    def get(self,start_year,semester):
        """
        获取课表
        :return:
        """
        payload = util.parser_token(request.headers['Authorization'])
        if payload.identify == Identify.STUDENT.value:#学生类型
            student = Student.objects(account=payload.username).first()
            if not student.syllabus.get(start_year+'0'+str(semester)): #数据库中没有这一学期的课表
                ret_val = util.get_syllabus_page(payload.username,student.password,start_year,semester)
                if not ret_val.status == Status.SUCCESS.value:
                    return syllabus_result(failed,msg=ret_val.msg)
                parser = util.SyllabusParser(ret_val.content) #从学分制获取课表
                raw_lessons = parser.parse().lessons
                lessons = list()
                for data in raw_lessons:  #将课程保存到数据库中，同时保持单例性
                    lesson_id = data[0]
                    Lesson().save_from_rawdata(data,start_year,semester)
                    lessons.append(Lesson.objects(lesson_id=lesson_id).first())
                syllabus = Syllabus(year=start_year,semester=semester,lessons=lessons)
                student.syllabus[str(start_year)+'0'+str(semester)] = syllabus
                student.save()
                return syllabus_result(success,'got syllabus from credit',syllabus=lessons)
            else:
                syllabus = student.syllabus.get(start_year+'0'+str(semester)).lessons
                return syllabus_result(success,'got syllabus from database',syllabus=syllabus)

        #判断为教师类型(todo)
            return syllabus_result(success,'teacher should add lesson self')

    @token_check
    @add_args(parser,('classid',str))
    def post(self,start_year,semester):
        args = self.parser.parse_args()
        classid = args['classid']

        lesson = Lesson.objects(lesson_id=classid).first()
        payload = util.parser_token(request.headers['Authorization'])
        if payload.identify == Identify.STUDENT.value:
            person = Student.objects(account=payload.username).first()
        else:
            person = Teacher.objects(account=payload.username).first()

        if not person.syllabus.get(start_year+'0'+str(semester)):
            person.syllabus[start_year+'0'+str(semester)] = Syllabus(year=start_year,semester=semester,lessons=list())
            person.save()
        if lesson in person.syllabus[start_year+'0'+str(semester)]['lessons']:
            return syllabus_result(failed,msg='lesson exist')
        person.syllabus[start_year+'0'+str(semester)]['lessons'].append(lesson)
        person.save()
        return syllabus_result(success,syllabus=person.syllabus[start_year+'0'+str(semester)]['lessons'])


def syllabus_result(status_func,msg='',syllabus=list()):
    def lesson2dict(lesson):
        return  {
            'id':lesson.lesson_id,
            'name':lesson.name,
            'teacher':lesson.teacher,
            'credit':lesson.credit,
            'classroom':lesson.classroom,
            'start_week':lesson.start_week,
            'end_week':lesson.end_week,
            'schedule':lesson.schedule
        }

    if len(syllabus) > 0:
        classes = list()
        for lesson in syllabus:
            classes.append(lesson2dict(lesson))
        return status_func(msg,syllabuses=classes)
    return failed(msg,syllabuses=syllabus)

@api_route('/classinfo/studentlist/<string:classid>')
class StudentListResource(Resource):
    @token_check
    def get(self,classid):
        lesson = Lesson.objects(lesson_id=classid).first()
        if len(lesson['studentList']) == 0:
            ret_val = util.get_student_list_by_classId(classid)
            if not ret_val.status == Status.SUCCESS.value:
                return failed(ret_val.msg)
            lesson['studentList'] = ret_val.studentList
            lesson.save()
            return success(students=ret_val.studentList)
        else:
            return success(students=lesson['studentList'])

@api_route('/lesson/<string:classid>')
class LessonResource(Resource):
    def get(self,classid):
        lesson = Lesson.objects(lesson_id=classid).first()
        if lesson:
            return lesson_result(success,'found lesson in database',lesson=lesson)
        else:
            ret_val = util.get_lesson_info(classid)
            if not ret_val.status == Status.SUCCESS.value:
                return lesson_result(failed,msg='network error')
            lesson = Lesson().save_from_dict(ret_val.lesson_info)
            return lesson_result(success,'found data in network',lesson = lesson)

def lesson_result(status_func,msg='',lesson=None):
    lesson_info = dict()
    lesson_info['lesson'] = dict()
    if lesson:
        lesson_info['lesson'] = {
            'id':lesson.lesson_id,
            'name':lesson.name,
            'teacher':lesson.teacher,
            'credit':lesson.credit,
            'classroom':lesson.classroom,
            'start_week':lesson.start_week,
            'end_week':lesson.end_week,
            'schedule':lesson.schedule
        }
    return status_func(msg,**lesson_info)




