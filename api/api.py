#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:api.py
@time: 2016-01-01 19:59

RESTful API 处理模块

"""

from flask import Blueprint
from flask.ext.restful import Resource,Api
from app import app
import functools

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

@api_route('/')
class Index(Resource):
    def get(self):
        return {'data':'hello'}




