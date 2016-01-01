#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:run.py
@time: 2016-01-01 20:42
"""
from app import app
from api import api
from web import web

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)

