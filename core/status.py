#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:status.py
@time: 2016-01-05 16:07
@功能：规范化返回，status表示执行成功或失败，msg表示相应的信息，data表示返回的数据，推荐dict
"""
from enum import Enum,unique
from conf.config import Dict,toDict

@unique
class Status(Enum):
    SUCCESS = 'success'
    FAILED = 'failed'
    ERROR = 'error'

@unique
class Error(Enum):
    CONNECT_ERROR = 'connect error'

def success(msg='',data={}):
    if data:
        ret_val = {
            'status':Status.SUCCESS,
            'msg':msg,
            'data':data
        }
    else:
        ret_val = {
            'status':Status.SUCCESS,
            'msg':msg
        }
    return toDict(ret_val)

def failed(msg='',data={}):
    if data:
        ret_val =  {
            'status':Status.FAILED,
            'msg':msg,
            'data':data
        }
    else:
        ret_val =  {
            'status':Status.FAILED,
            'msg':msg
        }

    return toDict(ret_val)

def error(msg = '',data={}):
    if data:
        ret_val =  {
            'status':Status.ERROR,
            'msg':msg,
            'data':data
        }
    else:
        ret_val =  {
            'status':Status.ERROR,
            'msg':msg
        }
    return toDict(ret_val)
