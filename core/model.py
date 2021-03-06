#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:model.py
@time: 2016-01-02 00:19
"""
from core import util
from core.status import *
from datetime import datetime
from mongoengine import *
from conf.config import configs
from datetime import datetime
import time

connect(configs.db.name) #连接mongo

@unique
class Identify(Enum):
    STUDENT = 'student'
    TEACHER = 'teacher'

@unique
class LeaveType(Enum):
    OTHER = 0 #其他
    SICK = 1 #病假
    AFFAIR = 2 #事假

@unique
class DiscussionType(Enum):
    LESSON = 0
    WHOLE = 1

#请假
class Leave(Document):
    leaveid = StringField(unique=True) #id为: studentid+classid+leave_date
    studentid = StringField()
    studentname = StringField()
    classid = StringField()
    classname = StringField()
    verify = BooleanField(default=False)
    leave_type = IntField(default=LeaveType.OTHER.value)
    leave_reason = StringField(default='')
    leave_date = DateTimeField()

    def leaveTypeName(self):
        if self.leave_type == LeaveType.OTHER.value:
            return '其他'
        elif self.leave_type == LeaveType.SICK.value:
            return '病假'
        elif self.leave_type == LeaveType.AFFAIR.value:
            return '事假'

    def leaveDate(self):
        dateStr = datetime.strftime(self.leave_date,'%Y年%m月%d日 ')
        dateStr += util.getWeekStr(self.leave_date.weekday())
        return dateStr


    meta = {
        'indexes':[
            'leaveid',
            'studentid',
            'classid',
        ],
        'ordering':['leave_date']
    }

    def toDict(self):
        return {
            'studentid':self.studentid,
            'studentname':self.studentname,
            'classid':self.classid,
            'classname':self.classname,
            'verify':self.verify,
            'leave_type':self.leave_type,
            'leave_date':datetime.strftime(self.leave_date,'%Y%m%d'),
            'leave_reason':self.leave_reason
        }

class Lesson(Document):
    """

    """
    lesson_id = StringField(unique=True)
    name = StringField()
    credit = FloatField(default=0.0)
    teacher = StringField()
    classroom = StringField()
    start_week = IntField(default=1)
    end_week = IntField(default=16)
    schedule = DictField()
    studentList = ListField()
    signlog = MapField(ListField())
    # leavelog = MapField(ListField(EmbeddedDocumentField(Leave)))
    likeList = ListField(default=list())
    teacherRef = ListField(default=list())

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

    def save_from_rawdata(self,lesson,years,semester):
        """
        raw data是指包含一个lesson一个列表，
        如：['64417', '[EEG2009A]信号与系统', '4.0', '李旭涛/闫敬文', 'E阶梯教室204', '1 -14',
         '', '34', '', '34', '', '', '']
        :return:
        """
        Lid = lesson[0]
        if Lesson.objects(lesson_id=Lid).first(): #保证Lesson的单例性
            return
        self.lesson_id = Lid
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

    def save_from_dict(self,lesson_dict):
        Lid = lesson_dict['lesson_id']
        if Lesson.objects(lesson_id=Lid).first():
            return
        self.lesson_id = lesson_dict['lesson_id']
        self.name = lesson_dict['name']
        self.teacher = lesson_dict['teacher']
        self.classroom = lesson_dict['classroom']
        self.start_week = lesson_dict['start_week']
        self.end_week = lesson_dict['end_week']
        self.schedule = lesson_dict['schedule']
        self.save()
        return self


    def exist(self,leeson_id,start_year,semester):
        return Lesson.objects(leeson_id).first()

    def get_lesson_time_str(self,now):
        weekday = now.weekday()
        if weekday == 6:
            weekday = 0
        else:
            weekday += 1
        lesson_time = self.schedule[str(weekday)]
        if len(lesson_time) == 0:
            return None
        return lesson_time[1:] if lesson_time[0] in['单','双'] else lesson_time

    def is_lesson_time(self,now):
        lesson_time_str = self.get_lesson_time_str(now)
        if lesson_time_str is None:
            return False #当天没课
        else:
            for t in lesson_time_str:
                ltime = datetime(year=now.year,month=now.month,day=now.day,
                                 hour=configs.lesson_time[t].hour,
                                 minute=configs.lesson_time[t].minute)
                if 0 <= (now - ltime).total_seconds() <= configs.lesson_time.duration * 60:
                    print('sign in %s'%t)
                    return True
            return False

    def is_leave_time_avaliable(self,now,leave_date):
        #请假时间是否有效：请假当天是否有课程？现在是否在课程开始之前？
        if leave_date.date() < now.date():
            return False
        lesson_time_str = self.get_lesson_time_str(leave_date)
        if lesson_time_str is None:
            return False #请假当天没课，请假时间无效
        lesson_start_time_str = lesson_time_str[0]
        lesson_start_time = datetime(year=leave_date.year,month=leave_date.month,day=leave_date.day,
                                     hour=configs.lesson_time[lesson_start_time_str].hour,
                                     minute=configs.lesson_time[lesson_start_time_str].minute)

        return lesson_start_time >= now


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
    deviceid = StringField()
    token = StringField()
    name = StringField()
    email = StringField()
    syllabus = MapField(EmbeddedDocumentField(Syllabus))

class Student(Document):
    account = StringField(required=True,unique=True)
    password  = StringField(required=True)
    deviceid = StringField()

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
    signlog = MapField(ListField())
    # leavelog = MapField(ListField(EmbeddedDocumentField(Leave)))

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

    def update_or_create(account,password,token):
        s = Student.objects(account = account).first()
        if s:
            #update
            s.password = password
            s.token = token
            s.save()
        else:
            #create
            s = Student(account=account,password=password,token=token)
        return s

class ClassRoom(Document):
    roomid = StringField(required=True)
    roomname = StringField(required=True,unique=True)
    roomtype = StringField()
    roommac = ListField(default=[roomname])


class Discussion(Document):
    type = IntField(default=DiscussionType.LESSON.value)
    fromUserName = StringField()
    toUserName = StringField()
    content = StringField()
    createTime = DateTimeField()
    updateTime = DateTimeField()

    meta = {
        'indexes': [
            'toUserName',
            ('type','toUserName','createTime')
        ],
        'ordering': ['createTime']
    }

    def toDict(self):
        datetime.now().time()
        return {
            'type':self.type,
            'fromUserName':self.fromUserName,
            'toUserName':self.toUserName,
            'content':self.content,
            'createTime':datetime.strftime(self.createTime,'%Y-%m-%d %H:%M:%S'),
            'updateTime':datetime.strftime(self.updateTime,'%Y-%m-%d %H:%M:%S')
        }

class Homework(Document):
    fromUserName = StringField()
    toUserName = StringField()
    title = StringField()
    content = StringField()
    deadline = DateTimeField()
    createTime = DateTimeField()
    updateTime = DateTimeField()

    meta = {
        'indexes': [
            'toUserName',
            'deadline',
            ('toUserName','createTime')
        ],
        'ordering': ['createTime']
    }

    def toDict(self):
        return {
            'fromUserName':self.fromUserName,
            'toUserName':self.toUserName,
            'title':self.title,
            'content':self.content,
            'deadline':datetime.strftime(self.deadline,'%Y-%m-%d'),
            'createTime':datetime.strftime(self.createTime,'%Y-%m-%d %H:%M:%S'),
            'updateTime':datetime.strftime(self.updateTime,'%Y-%m-%d %H:%M:%S')
        }

#一个账号可以登陆多个设备，但是一个设备只能登陆一个账号
#一个账号可以登陆多个设备，是为了换手机后仍能正常使用；
#一个设备只能登陆一个账号，是为了防止代签到的情况发生
class Device(Document):
    username = StringField(required=True)
    deviceId = StringField(required=True,unique=True)

    meta = {
        'indexes':[
            'username',
            'deviceId'
        ]
    }
