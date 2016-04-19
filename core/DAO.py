#!/usr/bin/python3
# -*- coding: utf-8 -*-

"""
@author: sharpdeep
@file:DAO.py
@time: 2016-04-04 17:35
"""
from datetime import datetime
from core.model import *

def isTeacher(payload):
    return payload.identify == Identify.TEACHER.value

def isStudent(payload):
    return payload.identify == Identify.STUDENT.value

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

def getDevicesByUsername(username):
    return Device.objects(username=username)

def getDeviceById(deviceId):
    return Device.objects(deviceId=deviceId)

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
    devices = getDevicesByUsername(payload.username)
    if devices:
        return deviceId in [device.deviceId for device in devices]
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

def isAskLeaveBeforeSign(username,classid):
    #签到时检查是否有请假
    student = get_student(account=username)
    if student is None:
        return None
    leave_list = student.leavelog.get(datetime.now().strftime('%Y%m%d'))
    if leave_list:
        return True if classid in [leave.classid for leave in leave_list] else False
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
    sign_student_list.append({'student_id':username,'student_name':student.name})
    lesson.signlog[now.strftime('%Y%m%d')] = sign_student_list
    lesson.save()

    sign_class_list = student.signlog.get(now.strftime('%Y%m%d'))
    if not sign_class_list:
        sign_class_list = list()
    sign_class_list.append({'lesson_id':classid,'lesson_name':lesson.name})
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

    leave.studentname = student.name
    leave.classname = lesson.name

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

def getLessonSignLog(classid,dateStr):
	lesson = get_or_create_lesson(classid)
	if lesson is None:
		return None
	if dateStr == 'all':
		return lesson.signlog
	signList = lesson.signlog.get(dateStr)
	return {dateStr:signList} if signList else None

def getLessonSignListCount(classid,dateStr):
	signlog = getLessonSignLog(classid,dateStr)
	if signlog is None or not isinstance(signlog,dict):
		return 0
	count = 0
	for v in signlog.values():
		count += len(v)
	return count

def getStudentSignLog(username,dateStr):
	student = get_student(account=username)
	if student is None:
		return None
	if dateStr == 'all':
		return student.signlog
	signList = student.signlog.get(dateStr)
	return {dateStr:signList} if signList else None

def getStudentSignLogCount(username,dateStr):
	signlog = getStudentSignLog(username,dateStr)
	if signlog is None or not isinstance(signlog,dict):
		return 0
	count = 0
	for v in signlog.values():
		count += len(v)
	return count

def getLessonLeaveLog(classid,dateStr):
	lesson = get_or_create_lesson(classid)
	if lesson is None:
		return None
	if dateStr == 'all':
		return lesson.leavelog
	leaveList = lesson.leavelog.get(dateStr)
	return {dateStr:leaveList} if leaveList else None

def getLessonLeaveLogCount(classid,dateStr):
	leavelog = getLessonLeaveLog(classid,dateStr)
	if leavelog is None or not isinstance(leavelog,dict):
		return 0
	count = 0
	for v in leavelog.values():
		count += len(v)
	return count

def getStudentLeaveLog(username,dateStr):
	student = get_student(account=username)
	if student is None:
		return None
	if dateStr == 'all':
		return student.leavelog
	leaveList = student.leavelog.get(dateStr)
	return {dateStr:leaveList} if leaveList else None

def getStudentLeaveLogCount(username,dateStr):
	leavelog = getStudentLeaveLog(username,dateStr)
	if leavelog is None or not isinstance(leavelog,dict):
		return 0
	count = 0
	for v in leavelog.values():
		count += len(v)
	return count

def getUserSyllabus(user,start_year,semester):
    syllabus = user.syllabus.get(start_year+'0'+str(semester))
    if not syllabus:
        return None
    return syllabus.lessons


def isSyllabusConflict(lesson,lessons):
    times = [(k,[t for t in v]) for k,v in lesson.schedule.items() if not len(v) == 0]
    print(times)
    for l in lessons:
        for t in times:
            for i in t[1]:
                if i in l.schedule[t[0]]:
                    return True
    return False

def addLesson(user,start_year,semester,classid):
    lesson = get_or_create_lesson(classid)
    syllabus = getUserSyllabus(user,start_year,semester)
    if lesson is None:
        return None
    if syllabus is None:
        user.syllabus[start_year+'0'+str(semester)] = Syllabus(year=start_year,semester=semester,lessons=list())
        user.save()
    if lesson in user.syllabus[start_year+'0'+str(semester)]['lessons']:
        return False

    conflict_check_val = isSyllabusConflict(lesson,getUserSyllabus(user,start_year,semester))
    if conflict_check_val:
        print("课程时间有冲突")
        return False

    user.syllabus[start_year+'0'+str(semester)]['lessons'].append(lesson)
    user.save()
    return True

def isLikeLessonBefore(username,classid):
    lesson = get_or_create_lesson(classid)
    if lesson is None:
        return None

    if not lesson.likeList:
        lesson.likeList = list()
        lesson.save()
        return False

    return True if username in lesson.likeList else False

def likeLesson(username,classid):
    lesson = get_or_create_lesson(classid)
    if lesson is None:
        return None

    if not lesson.likeList:
        lesson.likeList = list()
        lesson.save()

    lesson.likeList.append(username)
    lesson.save()
    return True

def getLessonLikeListCount(classid):
    lesson = get_or_create_lesson(classid)
    if lesson is None:
        return None

    return 0 if not lesson.likeList else len(lesson.likeList)

def makeLessonDiscussion(fromUserName,toLesson,content):
    discussion = Discussion(type=DiscussionType.LESSON.value,fromUserName=fromUserName,toUserName=toLesson,content=content)
    now = datetime.now()
    discussion.createTime = now
    discussion.updateTime = now
    discussion.save()

def getLessonDiscussion(toLesson,start_index):
    return [discussion for discussion in Discussion.objects(type=DiscussionType.LESSON.value,toUserName=toLesson)[start_index:]]

def makeHomework(teacherName,toLesson,title,content,deadline):
    homework = Homework(fromUserName=teacherName,toUserName=toLesson,title=title,content=content)
    homework.deadline = datetime.strptime(deadline,'%Y%m%d')
    now = datetime.now()
    homework.createTime = now
    homework.updateTime = now
    homework.save()

def homeworkDeadlineCheck(deadline):
    nowDate = datetime.now().date()
    deadlineDate = datetime.strptime(deadline,'%Y%m%d').date()

    return True if deadlineDate > nowDate else False

def getHomework(toLesson,start_index):
    return [homework for homework in Homework.objects(toUserName=toLesson)[start_index:]]

def getDeviceIds(username):
    devices = getDevicesByUsername(username)
    if devices:
        return '/'.join([device.deviceId for device in devices])
    return ''

def isDeviceExist(deviceId):
    return True if getDeviceById(deviceId) else False

def bindDevice(username,deviceId):
    device = Device(username=username,deviceId=deviceId)
    device.save()