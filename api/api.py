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
from core.model import *
from core.status import *
from core import util

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

"""
@api_route('/auth')
class Auth(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('username',str),('password',str))
    def post(self):
        args = self.parser.parse_args()
        username = args['username']
        passwd = args['password']

        auth_result = util.authenticate(username,passwd)
        if auth_result:
            return {'data':'success'}
        elif isinstance(auth_result,bool):
            return {'data':'faild'}
        else:
            return{'data':'connect error'}
"""

@api_route('/auth')
class Auth(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('identify',str),('username',str),('password',str))
    def post(self):
        args = self.parser.parse_args()
        identify = args['identify']
        username = args['username']
        password = args['password']
        if identify == 'student': #如果是学生，首先判断是否在数据库中，是的话直接数据库auth否则通过学分制，同时缓存
            student = Student.objects(account=username)
            if not student:#不在数据库中
                ret_val = util.authenticate(username,password)
                if not ret_val.status == Status.SUCCESS.value:
                    return error(Error.CONNECT_ERROR.value)

                ret_val = util.get_student_info_page(username,password)
                info_page = ret_val.data.content
                parser = util.StudentInfoParser(info_page,username,password)
                info = parser.parse()

                student = Student() #存到数据库中
                student.save_from_dict(info)
                """
                todo:1.生成token，存到数据库中；2.如果用户在数据库中，更新token
                """
            return success('auth!')
        elif identify == 'teacher':
            return success('teacher!')
        else:
            return error(Error.ARGUMENT_ERROR.value)




