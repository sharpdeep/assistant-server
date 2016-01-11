#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:api.py
@time: 2016-01-01 19:59

RESTful API 处理模块

"""

from flask import Blueprint
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

@api_route('/auth')
class Auth(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('username',str),('password',str)) #只提供账号和密码，账号类型由服务器判别(todo)
    def post(self):
        args = self.parser.parse_args()
        username = args['username']
        password = args['password']
        token = util.gen_token(username)

        teacher = Teacher.objects(account=username,password=password).first()
        if teacher: #判断为教师账号
            teacher.token = token #更新token
            teacher.save()
            return auth_result(success,'auth teacher from database',token,Identify.TEACHER.value)

        #不在教师数据库中，那么就可能是学生账号或非法账号
        student = Student.objects(account=username,password=password).first()
        if student: #学生类型,并在数据库中
            student.token = token #更新token
            student.save()
            return auth_result(success,'auth student from database',token,Identify.STUDENT.value)
        else: #数据库中找不到，需要用到学分制查询
            ret_val = util.authenticate(username,password)
            if ret_val.status == Status.SUCCESS.value: #验证成功，缓存info到数据库
                ret_val = util.get_student_info_page(username,password)
                if ret_val.status == Status.SUCCESS.value:
                    parser = util.StudentInfoParser(ret_val.content)
                    ret_val = parser.parse()
                    student = Student(account=username,password=password,token=token)
                    student.save_from_dict(ret_val.info) #顺便存储学生信息
                    return auth_result(success,'auth from credit',token,Identify.STUDENT.value)
                else:
                    return auth_result(failed,'failed to get student info')
            else:
                    return auth_result(failed,'failed to login credit')

def auth_result(status_func,msg='',token='',identify=''):
    return status_func(msg,data={'token':token,'identify':identify})







