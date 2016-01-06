#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:model.py
@time: 2016-01-02 00:19
"""
from mongoengine import *
from conf.config import configs

connect(configs.db.name) #连接mongo

class Lesson(Document):
    """
    备忘：lesson_id采用学年+学期+班号，如64417->20130164417？
    """
    lesson_id = StringField(unique=True)
    name = StringField()
    credit = FloatField(default=0.0)
    teacher = StringField()
    classroom = StringField()
    start_week = IntField(default=1)
    end_week = IntField(default=16)
    schedule = DictField()


    def __str__(self):
        lesson_info = '班号:\t'+self.lesson_id+'\t\n'+\
                      '课程名称:\t'+self.name+'\t\n'+\
                      '课程学分:\t'+str(self.credit)+'\t\n'+\
                      '教师:\t'+self.teacher+'\t\n'+\
                      '课室:\t'+self.classroom+'\t\n'+\
                      '起止周:\t'+str(self.start_week)+'-'+\
                      str(self.end_week)+'\t\n'
        schedule_info = ''
        for weekday,time in self.schedule.items():
            if not time == '':
                schedule_info += '周'+str(weekday)+':\t'+time+'\t\n'
        lesson_info += schedule_info
        return lesson_info

    def save_from_rawdata(self,lesson):
        """
        raw data是指包含一个lesson一个列表，
        如：['64417', '[EEG2009A]信号与系统', '4.0', '李旭涛/闫敬文', 'E阶梯教室204', '1 -14',
         '', '34', '', '34', '', '', '']
        :return:
        """
        self.lesson_id = lesson[0]
        self.name = lesson[1]
        self.credit = float(lesson[2])
        self.teacher = lesson[3]
        self.classroom = lesson[4]
        duration = lesson[5].split('-')
        self.start_week = int(duration[0])
        self.end_week = int(duration[1])
        for i in range(7):
            self.schedule[str(i)] = lesson[i+6]
        self.save()

class Syllabus(EmbeddedDocument):
    year = StringField()
    semester = IntField()
    lessons = ListField(ReferenceField(Lesson))

class User(Document):
    user_name = StringField(required=True,unique=True)
    password  = StringField(required=True)
    identity = StringField(choices=('student','teacher'),required=True)
    user_id = StringField(unique=True) #学号是唯一的
    grade = StringField() #哪一级
    syllabus = MapField(EmbeddedDocumentField(Syllabus)) #key为学年+学期，value为读音课表




