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

#请假
class Leave(EmbeddedDocument):
    studentid = StringField()
    classid = StringField()
    leave_type = IntField(default=LeaveType.OTHER.value)
    leave_reason = StringField(default='')
    leave_date = DateTimeField()

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
    leavelog = MapField(ListField(EmbeddedDocumentField(Leave)))

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
        return lesson_time

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
        lesson_start_time = datetime(year=now.year,month=now.month,day=now.day,
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
    leavelog = MapField(ListField(EmbeddedDocumentField(Leave)))

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

def get_or_create_lesson(classid):
    lesson = Lesson.objects(lesson_id=classid).first()
    if not lesson:
        ret_val = util.get_lesson_info(classid)
        if not ret_val.status == Status.SUCCESS.value:
            return None
        lesson = Lesson().save_from_dict(ret_val.lesson_info)
    return lesson

def get_student(**kwargs):
    return Student.objects(**kwargs).first()

def get_teacher(**kwargs):
    return Teacher.objects(**kwargs).first()

def get_or_create_classroom(classid,mac=["mac"]):
    lesson = get_or_create_lesson(classid)
    if lesson is None:
        return None
    roomname = lesson.classroom
    room = ClassRoom.objects(roomname=roomname).first()
    if not room:
        ret_val = util.get_class_room_info(classid)
        if not ret_val.status == Status.SUCCESS.value:
            return None
        info = ret_val.classroom_info
        room = ClassRoom(roomid=info.roomid,roomname=info.roomname,roomtype=info.roomtype)
        room.roommac = mac
        room.save()
    return room

def isLessonTime(classid):
    lesson = get_or_create_lesson(classid)
    if not lesson:
        return None #失败(可能是班号错误)

    return lesson.is_lesson_time(datetime.now())

def inClassRoom(classid,mac):
    room = get_or_create_classroom(classid)
    if room is None:
        return None
    return mac in room.roommac

def deviceCheck(payload,deviceId):
    identify = payload.identify
    username = payload.username

    if identify == Identify.STUDENT.value:
        person = get_student(account=username)
    else:
        person = get_teacher(account=username)

    if person:
        return person.deviceid == deviceId
    return None

def isSignRepeat(username,classid):
    lesson = get_or_create_lesson(classid)
    if lesson is None:
        return None
    now = datetime.now()
    sign_student_list = lesson.signlog.get(now.strftime('%Y%m%d'))
    if sign_student_list and username in sign_student_list:
        return True
    return False

def sign(username,classid):
    lesson = get_or_create_lesson(classid)
    student = get_student(account=username)
    if lesson is None or student is None:
        return None
    now = datetime.now()
    sign_student_list = lesson.signlog.get(now.strftime('%Y%m%d'))
    if not sign_student_list:
        sign_student_list = list()
    sign_student_list.append(username)
    lesson.signlog[now.strftime('%Y%m%d')] = sign_student_list
    lesson.save()

    sign_class_list = student.signlog.get(now.strftime('%Y%m%d'))
    if not sign_class_list:
        sign_class_list = list()
    sign_class_list.append(lesson.lesson_id)
    student.signlog[now.strftime('%Y%m%d')] = sign_class_list
    student.save()

    return True

def isAskLeaveRepeat(leave):
    lesson = get_or_create_lesson(leave.classid)
    if lesson is None:
        return None
    leave_list = lesson.leavelog.get(leave.leave_date.strftime('%Y%m%d'))
    if leave_list and leave.studentid in [l.studentid for l in leave_list]:
        return True
    return False

def leaveTimeCheck(leave):
    lesson = get_or_create_lesson(leave.classid)
    if lesson is None:
        return None

    return lesson.is_leave_time_avaliable(datetime.now(),leave.leave_date)


def askLeave(leave):
    lesson = get_or_create_lesson(leave.classid)
    student = get_student(account=leave.studentid)
    if lesson is None or student is None:
        return None

    lesson_leave_list = lesson.leavelog.get(leave.leave_date.strftime('%Y%m%d'))
    if not lesson_leave_list:
        lesson_leave_list = list()
    lesson_leave_list.append(leave)
    lesson.leavelog[leave.leave_date.strftime('%Y%m%d')] = lesson_leave_list
    lesson.save()

    student_leave_list = student.leavelog.get(leave.leave_date.strftime('%Y%m%d'))
    if not student_leave_list:
        student_leave_list = list()
    student_leave_list.append(leave)
    student.leavelog[leave.leave_date.strftime('%Y%m%d')] = student_leave_list
    student.save()
    #todo 发送邮件给老师，更新老师的model
    return True
