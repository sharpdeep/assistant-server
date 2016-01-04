#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:app.py
@time: 2016-01-01 23:11
"""
from flask import Flask
from conf.config import configs
import logging
from  logging.handlers import RotatingFileHandler

logger = logging.getLogger(configs.app.log.name)
logfileHandler = RotatingFileHandler(configs.app.log.logFile,
                                     maxBytes=configs.app.log.maxBytes,
                                     backupCount=configs.app.log.backupCount)
logfileHandler.setFormatter(logging.Formatter('[%(asctime)s]  %(levelname)s  "%(message)s"'))
logfileHandler.setLevel(configs.app.log.logLevel)
logger.addHandler(logfileHandler)
logger.setLevel(configs.app.log.logLevel)


app = Flask(__name__)

