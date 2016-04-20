#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:api.py
@time: 2016-01-01 19:59

RESTful API 处理模块

"""

from flask import Blueprint,request
from flask.ext.restful import Resource,Api,reqparse
from app import app
import functools
from enum import Enum,unique
from core.model import *
from core.status import *
from core.DAO import *
from core import util

api = Api(app)
api_prefix = '/api'

error_code = configs.error_code

def api_route(*urls,**kwargs):
    """
    装饰器,将Resources类与url关联起来,并添加前缀
    :param urls:一个或多个path,path不能为'/api'?
    :param kwargs:
    :return:
    """
    def decorator(cls):
        @functools.wraps(cls)
        def wrapper(*args,**kw):
            return cls(*args,**kw)
        #参数检查
        if len(urls) < 1:
            raise ValueError('no url in urls for Resource:%s'%cls.__name__)
        #添加前缀
        prefix_urls = list(urls)
        for i in range(len(prefix_urls)):
            prefix_urls[i] = api_prefix+prefix_urls[i]
        api.add_resource(cls,*prefix_urls,**kwargs)
        return wrapper
    return decorator

def add_args(parser,*arguments):
    """
    装饰器，方便post和put等参数解析
    :param parser:
    :param arguments:
    :return:
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args,**kwargs):
            return func(*args,**kwargs)
        for arg in arguments:
            if not isinstance(arg,tuple):
                raise ValueError('arg in arguments should be tuple')
            arg_list = list()
            kw = dict()
            for i in arg:
                if isinstance(i,dict):
                    kw = i
                else:
                    arg_list.append(i)
            parser.add_argument(*arg_list,**kw)
        return wrapper
    return decorator

def token_check(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        if not request.headers.get('Authorization'):
            return base_result(failed,msg='no token',error_code=error_code.token_no_exist_error)

        token = request.headers['Authorization']
        # print(token)
        payload = util.parser_token(token)
        if payload is None:
            return base_result(failed,msg='no token',error_code=error_code.token_no_exist_error)
        print('['+payload.identify+']'+payload.username+' auth in '+str(datetime.fromtimestamp(payload.timestamp)))
        nowtime = int(datetime.now().timestamp())
        if not payload:
            return base_result(failed,msg='illegal token',error_code=error_code.token_illegal_error)
        if nowtime - payload.timestamp > configs.app.exprire:
            return base_result(failed,msg='expire token',error_code=error_code.token_expire_error)
        else:
            return func(*args,**kwargs)
    return wrapper

#不进行token合法性检查
def only_student(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        payload = util.parser_token(request.headers['Authorization'])
        if payload.identify == Identify.TEACHER.value:
            return base_result(failed,msg="该接口只允许学生访问",error_code=error_code.identify_only_student_error)
        return func(*args,**kwargs)
    return wrapper

#不进行token合法性检查
def only_teacher(func):
    @functools.wraps(func)
    def wrapper(*args,**kwargs):
        payload = util.parser_token(request.headers['Authorization'])
        if payload.identify == Identify.STUDENT.value:
            return base_result(failed,msg="该接口只允许教师访问",error_code=error_code.identify_only_teacher_error)
        return func(*args,**kwargs)
    return wrapper

@api_route('/auth')
class AuthResource(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('username',str),('password',str))
    def post(self):
        args = self.parser.parse_args()
        username = args['username']
        password = args['password']

        teacher = Teacher.objects(account=username,password=password).first()
        if teacher: #判断为教师账号
            token = util.gen_token(username,Identify.TEACHER.value)
            teacher.token = token #更新token
            teacher.save()
            return auth_result(success,'auth teacher from database',token,Identify.TEACHER.value)

        # #不在教师数据库中，那么就可能是学生账号或非法账号
        token = util.gen_token(username,Identify.STUDENT.value)
        ret_val = util.authenticate(username,password)
        if ret_val.status == Status.SUCCESS.value: #验证成功，缓存info到数据库
            ret_val = util.get_student_info_page(username,password)
            if ret_val.status == Status.SUCCESS.value:
                parser = util.StudentInfoParser(ret_val.content)
                ret_val = parser.parse()
                student = Student.update_or_create(account=username,password=password,token=token)
                student.save_from_dict(ret_val.info) #顺便存储学生信息
                return auth_result(success,'auth from credit',token,Identify.STUDENT.value)
            else:
                return auth_result(failed,'failed to get student info')
        else:
                return auth_result(failed,'failed to login credit')

@api_route('/syllabus/<string:start_year>/<int:semester>')
class SyllabusResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    def get(self,start_year,semester):
        """
        获取课表
        :return:
        """
        payload = util.parser_token(request.headers['Authorization'])
        if payload.identify == Identify.STUDENT.value:#学生类型
            student = Student.objects(account=payload.username).first()
            if not student.syllabus.get(start_year+'0'+str(semester)): #数据库中没有这一学期的课表
                ret_val = util.get_syllabus_page(payload.username,student.password,start_year,semester)
                if not ret_val.status == Status.SUCCESS.value:
                    return syllabus_result(failed,msg=ret_val.msg)
                parser = util.SyllabusParser(ret_val.content) #从学分制获取课表
                raw_lessons = parser.parse().lessons
                lessons = list()
                for data in raw_lessons:  #将课程保存到数据库中，同时保持单例性
                    lesson_id = data[0]
                    Lesson().save_from_rawdata(data,start_year,semester)
                    lessons.append(Lesson.objects(lesson_id=lesson_id).first())
                syllabus = Syllabus(year=start_year,semester=semester,lessons=lessons)
                student.syllabus[str(start_year)+'0'+str(semester)] = syllabus
                student.save()
                return syllabus_result(success,'got syllabus from credit',syllabus=lessons)
            else:
                syllabus = student.syllabus.get(start_year+'0'+str(semester)).lessons
                return syllabus_result(success,'got syllabus from database',syllabus=syllabus)
        else:
            teacher = get_teacher(account=payload.username)
            if not teacher:
                return syllabus_result(error,'不存在该用户')
            syllabus = getUserSyllabus(teacher,start_year,semester)
            if syllabus is None:
                return syllabus_result(failed,'not exist syllabus')
            return syllabus_result(success,'数据库中有课表数据',syllabus=syllabus)

    @token_check
    @add_args(parser,('classid',str))
    def post(self,start_year,semester):
        args = self.parser.parse_args()
        classid = args['classid']
        payload = util.parser_token(request.headers['Authorization'])

        if isStudent(payload):
            person = get_student(account=payload.username)
        else:
            person = get_teacher(account=payload.username)

        ret = addLesson(person,start_year,semester,classid)

        if ret:
            syllabus = getUserSyllabus(person,start_year,semester)
            return syllabus_result(success,'添加成功',syllabus=syllabus)
        elif isinstance(ret,bool):
            return syllabus_result(failed,'添加失败')

        return syllabus_result(error,'服务器未知错误')


@api_route('/classinfo/studentlist/<string:classid>')
class StudentListResource(Resource):
    @token_check
    def get(self,classid):
        lesson = get_or_create_lesson(classid)
        if len(lesson['studentList']) == 0:
            ret_val = util.get_student_list_by_classId(classid)
            if not ret_val.status == Status.SUCCESS.value:
                return failed(ret_val.msg)
            lesson['studentList'] = ret_val.studentList
            lesson.save()
            return success(students=ret_val.studentList)
        else:
            return success(students=lesson['studentList'])

@api_route('/lesson/<string:classid>')
class LessonResource(Resource):
    def get(self,classid):
        lesson = get_or_create_lesson(classid)
        if lesson:
            return lesson_result(success,lesson = lesson)
        return lesson_result(failed,msg='network error')

@api_route('/sign')
class SignResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    @only_student
    @add_args(parser,('classid',str),('device_id',str),('mac',str))
    def post(self):
        args = self.parser.parse_args()
        device_id = args['device_id']
        mac = args['mac']
        classid = args['classid']
        payload = util.parser_token(request.headers['Authorization'])

        device_check_val = deviceCheck(payload,device_id)
        if device_check_val: #是本人
            time_check_val = isLessonTime(classid)
            if time_check_val: #时间正确
                room_check_val = inClassRoom(classid,mac)
                if room_check_val: #在教室内
                    leave_check_val = isAskLeaveBeforeSign(payload.username,classid)
                    if leave_check_val:
                        return sign_result(error,msg='已经请假过了,不用签到',error_code=error_code.sign_leave_before_error)
                    elif isinstance(leave_check_val,bool):
                        repeat_check_val = isSignRepeat(payload.username,classid)
                        if repeat_check_val:
                            return sign_result(error,msg='重复签到',error_code=error_code.sign_repeat_error)
                        elif isinstance(repeat_check_val,bool):
                            if sign(payload.username,classid):#没有重复签到
                                return sign_result(success,msg='签到成功')
                elif isinstance(room_check_val,bool):
                        return sign_result(failed,msg='签到地点错误',error_code=error_code.sign_room_error)
            elif isinstance(time_check_val,bool):
                    return sign_result(failed,msg='签到时间不对',error_code=error_code.sign_time_error)
        elif isinstance(device_check_val,bool): #失败检查失败
            return sign_result(failed,msg='不是本人设备',error_code=error_code.sign_device_error)
        return sign_result(error,msg='未知错误',error_code=error_code.unknow_error)

@api_route('/signlist/lesson/<string:classid>/<string:date>')
class LessonSignListResource(Resource):
    def get(self,classid,date):
        signlog = getLessonSignLog(classid,date)
        if signlog is None:
            return signlist_result(failed,msg='不存在签到记录',error_code=error_code.signlist_exist_error)
        else:
            return signlist_result(success,signlog=signlog)

@api_route('/signlist/lesson/count/<string:classid>/<string:date>')
class LessonSignListCountResource(Resource):
    def get(self,classid,date):
        return signlist_count_result(success,msg=str(getLessonSignListCount(classid,date)))

@api_route('/signlist/student/<string:username>/<string:date>')
class StudentSignListResource(Resource):
    def get(self,username,date):
        signlog = getStudentSignLog(username,date)
        if signlog is None:
            return signlist_result(failed,msg='不存在签到记录',error_code=error_code.signlist_exist_error)
        else:
            return signlist_result(success,signlog=signlog)

@api_route('/signlist/student/count/<string:username>/<string:date>')
class StudentSignListCountResource(Resource):
    def get(self,username,date):
        return signlist_count_result(success,msg=str(getStudentSignLogCount(username,date)))

@api_route('/leavelist/lesson/<string:classid>/<string:date>')
class LessonLeaveListResource(Resource):
    def get(self,classid,date):
        leavelog = getLessonLeaveLog(classid,date)
        if leavelog is None:
            return leavelist_result(failed,msg='不存在请假记录',error_code=error_code.leavelist_exist_error)
        else:
            return leavelist_result(success,leavelog=leavelog)

@api_route('/leavelist/lesson/count/<string:classid>/<string:date>')
class LessonLeaveListCountResource(Resource):
    def get(self,classid,date):
        return leavelist_count_result(success,msg=str(getLessonLeaveLogCount(classid,date)))

@api_route('/leavelist/student/<string:username>/<string:date>')
class StudentLeaveListResource(Resource):
    def get(self,username,date):
        leavelog = getStudentLeaveLog(username,date)
        if leavelog is None:
            return leavelist_result(failed,msg='不存在请假记录',error_code=error_code.leavelist_exist_error)
        else:
            return leavelist_result(success,leavelog=leavelog)

@api_route('/leavelist/student/count/<string:username>/<string:date>')
class StudentLeaveListCountResource(Resource):
    def get(self,username,date):
        return leavelist_count_result(success,msg=str(getStudentLeaveLogCount(username,date)))

@api_route('/leave')
class LeaveResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    @only_student
    @add_args(parser,('leave_date',str),('leave_type',int),('leave_reason',str),('classid',str))
    def put(self):
        payload = util.parser_token(request.headers['Authorization'])
        username = payload.username

        args = self.parser.parse_args()
        leave_date = datetime.strptime(args['leave_date'],'%Y%m%d')
        leave_type = args['leave_type']
        leave_reason = args['leave_reason']
        classid = args['classid']
        leaveid = mkLeaveId(username,classid,leave_date)

        time_check_val = leaveTimeCheck(classid,leave_date)
        if time_check_val:
            repeat_check_val = isAskLeaveRepeat(leaveid)
            if repeat_check_val:
                return leave_result(failed,msg='重复请假',error_code=error_code.leave_repeat_error)
            elif isinstance(repeat_check_val,bool):
                if askLeave(leaveid,username,classid,leave_type,leave_reason,leave_date):
                    return leave_result(success,msg='请假成功,等待老师同意')
        elif isinstance(time_check_val,bool):
            return leave_result(failed,msg='时间有问题',error_code=error_code.leave_time_error)
        return leave_result(failed,msg='未知错误',error_code=error_code.unknow_error)

@api_route('/like/lesson/<string:classid>')
class LessonLikeResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    def post(self,classid):
        payload = util.parser_token(request.headers['Authorization'])
        repeat_check_val = isLikeLessonBefore(payload.username,classid)
        if repeat_check_val:
            return lesson_like_result(failed,msg="重复点赞",error_code=error_code.like_lesson_repeat_error)
        elif isinstance(repeat_check_val,bool):
            like_ret = likeLesson(payload.username,classid)
            if like_ret:
                return lesson_like_result(success,msg="点赞成功")
            elif isinstance(like_ret,bool):
                return lesson_like_result(failed,msg="点赞失败",error_code=error_code.like_lesson_failed_error)

        return lesson_like_result(error,msg="未知错误",error_code=error_code.unknow_error)

    def get(self,classid):
        like_count_ret = getLessonLikeListCount(classid)
        if like_count_ret is None:
            return lesson_like_result(error,msg="未知错误",error_code=error_code.unknow_error)
        return lesson_like_result(success,msg=str(like_count_ret))


@api_route('/discussion/lesson/<string:classid>')
class LessonDiscussionResource(Resource):
    parser = reqparse.RequestParser()

    @add_args(parser,('fromUserName',str),('content',str))
    def put(self,classid):
        args = self.parser.parse_args()
        fromUserName = args['fromUserName']
        content = args['content']

        makeLessonDiscussion(fromUserName,classid,content)
        return base_result(success,msg='成功发表')

    @add_args(parser,('after',int))
    def get(self,classid):
        args = self.parser.parse_args()
        after_index = args['after']

        discussionList = getLessonDiscussion(classid,int(after_index))
        return lesson_discussion_result(success,discussions=discussionList)

@api_route('/homework/<string:classid>')
class HomeworkResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    @only_teacher
    @add_args(parser,('title',str),('content',str),('deadline',str))
    def put(self,classid):
        args = self.parser.parse_args()
        title = args['title']
        content = args['content']
        deadline = args['deadline']
        payload = util.parser_token(request.headers['Authorization'])
        if not homeworkDeadlineCheck(deadline):
            return base_result(failed,msg='截止日期出错',error_code=error_code.identify_homework_deadline_error)

        makeHomework(payload.username,classid,title,content,deadline)
        return base_result(success,msg='成功发布作业')

    @add_args(parser,('after',int))
    def get(self,classid):
        args = self.parser.parse_args()
        after_index = args['after']

        return homework_result(success,homeworks=getHomework(classid,int(after_index)))

@api_route('/device')
class DeviceResource(Resource):
    parser = reqparse.RequestParser()

    @token_check
    @only_student
    def get(self):
        payload = util.parser_token(request.headers['Authorization'])
        return base_result(success,msg=getDeviceIds(payload.username))

    @token_check
    @only_student
    @add_args(parser,('deviceid',str))
    def put(self):
        args = self.parser.parse_args()
        deviceId = args['deviceid']
        payload = util.parser_token(request.headers['Authorization'])


        if isDeviceExist(deviceId):
            return base_result(failed,msg='设备已经被绑定',error_code=error_code.device_bind_exist_error)
        bindDevice(payload.username,deviceId)
        return base_result(success,msg='绑定成功')


def auth_result(status_func,msg='',token='',identify=''):
    return status_func(msg,data={'token':token,'identify':identify})

def syllabus_result(status_func,msg='',syllabus=list()):
    def lesson2dict(lesson):
        return  {
            'id':lesson.lesson_id,
            'name':lesson.name,
            'teacher':lesson.teacher,
            'credit':lesson.credit,
            'classroom':lesson.classroom,
            'start_week':lesson.start_week,
            'end_week':lesson.end_week,
            'schedule':lesson.schedule
        }

    if len(syllabus) > 0:
        classes = list()
        for lesson in syllabus:
            classes.append(lesson2dict(lesson))
        return status_func(msg,syllabuses=classes)
    return failed(msg,syllabuses=syllabus)

def lesson_result(status_func,msg='',lesson=None):
    lesson_info = dict()
    lesson_info['lesson'] = dict()
    if lesson:
        lesson_info['lesson'] = {
            'id':lesson.lesson_id,
            'name':lesson.name,
            'teacher':lesson.teacher,
            'credit':lesson.credit,
            'classroom':lesson.classroom,
            'start_week':lesson.start_week,
            'end_week':lesson.end_week,
            'schedule':lesson.schedule
        }
    return status_func(msg,**lesson_info)

def base_result(status_func,msg='',error_code=configs.error_code.success):
    return status_func(msg,error_code=error_code)

def signlist_result(status_func,msg='',error_code=configs.error_code.success,signlog=dict()):
    logs = list()
    for date,signlist in signlog.items():
        sign = {'date':date}
        for s in signlist:
            sign.update(s)
            logs.append(sign)
    return status_func(msg,error_code=error_code,signlog=logs)

def leavelist_result(status_func,msg='',error_code=error_code.success,leavelog=dict()):
    logs = list()
    for date,leavelist in leavelog.items():
        leave = {'date':date}
        for l in leavelist:
            leave.update(l.toDict())
            logs.append(leave)
    return status_func(msg,error_code=error_code,leavelog=logs)

def lesson_discussion_result(status_func,msg='',error_code=error_code.success,discussions = list()):
    discussionList = list()
    for discussion in discussions:
        discussionList.append(discussion.toDict())

    return status_func(msg,error_code=error_code,discussionList=discussionList)

def homework_result(status_func,msg='',error_code=error_code.success,homeworks = list()):
    homeworkList = list()
    for homework in homeworks:
        homeworkList.append(homework.toDict())

    return status_func(msg,error_code=error_code,homeworkList=homeworkList)

sign_result = base_result
leave_result = base_result
signlist_count_result = base_result
leavelist_count_result = base_result
lesson_like_result = base_result

