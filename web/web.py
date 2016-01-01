#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:web.py
@time: 2016-01-01 21:18
"""

from flask import Blueprint

web = Blueprint('web',__name__,static_folder='static',
                template_folder='templates')

