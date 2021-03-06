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
    ARGUMENT_ERROR = 'argument error'

def success(msg='',**data):
    ret_val = {
        'status':Status.SUCCESS.value,
        'msg':msg,
    }
    ret_val.update(data)
    return toDict(ret_val)

def failed(msg='',**data):
    ret_val = {
        'status':Status.FAILED.value,
        'msg':msg,
    }
    ret_val.update(data)
    return toDict(ret_val)

def error(msg = '',**data):
    ret_val = {
        'status':Status.ERROR.value,
        'msg':msg,
    }
    ret_val.update(data)
    return toDict(ret_val)
