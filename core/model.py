#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:model.py
@time: 2016-01-02 00:19
"""
from mongoengine import *
from conf.config import configs
from datetime import datetime

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

class Teacher(Document):
    """
    教师账号采用后台注册方式
    """
    account = StringField(required=True,unique=True)
    password = StringField(required=True)
    token = StringField()
    name = StringField()
    syllabus = MapField(EmbeddedDocumentField(Syllabus))

class Student(Document):
    account = StringField(required=True,unique=True)
    password  = StringField(required=True)

    name = StringField()
    vid = StringField()
    address = StringField()
    student_id = StringField(unique=True) #学号是唯一的
    gender = StringField()
    birthday = DateTimeField()
    identify_id = StringField(unique=True)
    nation = StringField()
    college = StringField()
    major = StringField()
    grade = StringField()
    enrolmentdate = DateTimeField()
    tutor = StringField() #备忘：teacher model完成后做一个引用字段
    status = StringField() #学籍状态
    nativeplace = StringField() #籍贯
    familyphone = StringField() #家庭电话
    postalcode = StringField() #邮编

    token = StringField()
    syllabus = MapField(EmbeddedDocumentField(Syllabus)) #key为学年+学期，value为读音课表

    def save_from_dict(self,info):
        self.name = info['name']
        self.vid = info['vid']
        self.address = info['address']
        self.student_id = info['student_id']
        self.gender = info['gender']
        self.birthday = datetime.strptime(info['birthday'],'%Y%m%d')
        self.identify_id = info['identify_id']
        self.nation = info['nation']
        self.college = info['college']
        self.major = info['major']
        self.grade = info['grade']
        self.enrolmentdate = datetime.strptime(info['enrolmentdate'],'%Y%m%d')
        self.tutor = info['tutor']
        self.status = info['status']
        self.nativeplace = info['nativeplace']
        self.familyphone = info['familyphone']
        self.postalcode = info['postalcode']

        self.save()


