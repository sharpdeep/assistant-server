#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:state.py
@time: 2016-01-05 16:07
@功能：规范化返回，status表示执行成功或失败，msg表示相应的信息，data表示返回的数据，推荐dict
"""
from enum import Enum,unique

@unique
class State(Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    ERROR = 'error'

@unique
class Error(Enum):
    CONNECT_ERROR = 'connect error'

def success(msg='',data={}):
    if data:
        return {
            'status':State.SUCCESS,
            'msg':msg,
            'data':data
        }
    else:
        return {
            'status':State.SUCCESS,
            'msg':msg
        }

def failed(msg='',data={}):
    if data:
        return {
            'status':State.FAILED,
            'msg':msg,
            'data':data
        }
    else:
        return {
            'status':State.FAILED,
            'msg':msg
        }

def error(msg = '',data={}):
    if data:
        return {
            'status':State.ERROR,
            'msg':msg,
            'data':data
        }
    else:
        return {
            'status':State.ERROR,
            'msg':msg
        }
