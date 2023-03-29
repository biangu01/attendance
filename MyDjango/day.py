from . import dbfun,constants,pubFun,leave,ot
import time,calendar,json,datetime
from django.views.decorators.csrf import csrf_exempt
from dbModel.models import day as db_day
from dbModel.models import emp_info,genderDict,groupDict
from dbModel.models import special_calendar as sc
from dbModel import models
from django.core.paginator import Paginator


def dateInfo(date,needLastDay=False,emp=None):
    """
    根据输入的日期
    返回：
    1、输入日期的类型 1 - 平日 2 - 周末 3 - 节假日 4 - 特殊日期
    2、输入日期的工作时间，如果有特殊条件的，可以返回负数
    3、输入日期的上一个工作日
    """
    
    d = date.split("-")

    lastWorkDay = "" 
    
    holiday = dbfun.findSpecialHoliday(date).first()

    if holiday:
        if holiday.date_type == 1:
            dateType = 3
            workHours = 0
        else:
            workHours = workHourSpecialHolidayEmp(holiday,emp)
            dateType = 1 if holiday.work_hours > 0 else 2
    else:
        dateType, workHours = normalDayCheck(date)

    """
    if not holiday:
        
        dayNum = calendar.weekday(int(d[0]),int(d[1]),int(d[2]))

        if dayNum < 5 : #weekday
            workHours = constants.STATUTORY_WORKING_HOURS #8小时
            dateType = 1
        else:
            workHours = 0
            dateType = 2
    else:
        dateType = holiday[0].date_type
        holidayRange = holiday.used_for
        workHours = constants.STATUTORY_WORKING_HOURS #8小时
        
        #根据条件判断wh
        if holidayRange:
            holidayRangeDict = json.loads(holidayRange)
            if emp:
                gender = emp.gender
                groups = emp.group_rule_set.all()
                if "gender" in holidayRangeDict:
                    if gender == genderDict[holidayRangeDict["gender"]]:
                        workHours = holiday[0].work_hours
                if "group" in holidayRangeDict:
                    for group in groups:
                        if group.name.lower() in genderDict[holidayRangeDict["group"]]:
                            workHours = holiday[0].work_hours
                            break
            else:
                #一般走不到这里
                workHours = holiday[0].work_hours
        else:
            workHours = holiday[0].work_hours
            
        if dateType == 1 :
            dateType = 3
        elif workHours > 0 :
            if dateType == 3:
                dateType = 4
            else:
                dateType = 1
        else:
            dateType = 2
    """

    if needLastDay:
        #计算上一个工作日
        
        dt_format = "%Y-%m-%d"# %H:%M:%S"
        dayStamp = time.mktime(time.strptime(date,dt_format))

        dayStamp = dayStamp + 8*3600
        # time.gmtime 会返回包含时区的时间，所有这里要+8*3600
        #time库方法以秒为单位
        
        num = 1

        while num < 60:
            dayStamp = dayStamp - 3600*24

            tup = time.gmtime(dayStamp)
            day = time.strftime(dt_format,tup)
            
            holiday = dbfun.findSpecialHoliday(day).first()
            
            if holiday:
                wh = workHourSpecialHolidayEmp(holiday,emp)
                if wh > 0:
                    lastWorkDay = day
                    break
                elif wh < 0:
                    #不会出这种情况
                    if normalDayCheck(day)[1]>0:
                        lastWorkDay = day
                        break
                    else:
                        pass
                else:
                    pass
            else:
                if normalDayCheck(day)[1]>0:
                    lastWorkDay = day
                    break
                else:
                    pass
            num = num+1
            
        if lastWorkDay == "":
            lastWorkDay = day

        return dateType, workHours, lastWorkDay

    return dateType, workHours

def dayType(date,calculate=False):
    typ, wh = dateInfo(date)
    if typ == 1 or (typ == 4 and wh > 0):  # 平日
        txt = "平日"
        if calculate:
            return 1
    elif typ == 2 or (typ == 4 and wh == 0):  # 周末
        txt = "周末"
        if calculate:
            return 2
    elif typ == 3:  # 节假日
        txt = "节假日"
        if calculate:
            return 3
    else:
        txt = ""
    return txt

def workHourSpecialHolidayEmp(holiday,emp):
    holidayRange = holiday.used_for
    workHours = -1
    
    #根据条件判断wh
    if holidayRange:
        holidayRangeDict = json.loads(holidayRange)
        if emp:
            gender = emp.gender
            groups = emp.group_rule_set.all()
            if "gender" in holidayRangeDict:
                if gender == genderDict[holidayRangeDict["gender"]]:
                    workHours = holiday.work_hours_special
            if "group" in holidayRangeDict:
                for group in groups:
                    for s in holidayRangeDict["group"]:
                        if group.name.lower().startswith(s.lower()):
                            workHours = holiday.work_hours_special
                            break
                    if workHours >=0:
                        break
        if workHours < 0:
            workHours = holiday.work_hours
    else:
        workHours = holiday.work_hours_special if holiday.work_hours_special else holiday.work_hours

    return workHours

def normalDayCheck(date):
    d = date.split("-")
    dayNum = calendar.weekday(int(d[0]),int(d[1]),int(d[2]))

    if dayNum < 5 : #weekday
        workHours = constants.STATUTORY_WORKING_HOURS #8小时
        dateType = 1
    else:
        workHours = 0
        dateType = 2
        
    return dateType,workHours

@csrf_exempt
def calendarDay(request):
    json_result = json.loads(request.body)

    date = json_result['date']

    dateType, workHours, lastWorkDay = dateInfo(date,True)

    return pubFun.returnMsg(201,dateType=dateType,lastWorkDay=lastWorkDay)

@csrf_exempt
def calendarDay1(request):
    json_result = json.loads(request.body)

    date = json_result['date']

    if 'empID' not in json_result:
        return pubFun.returnMsg(208,"参数错误，请将当前页面截图后提交给Leader!")

    empID = json_result['empID']
    
    msg = pubFun.paraValidate(date=date,empID=empID)

    if msg:
        return pubFun.returnMsg(208,msg)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    dateType, workHours, lastWorkDay = dateInfo(date,True,emp)

    #工作日 1   休息日 2
    dateType = 1 if workHours > 0 else 2

    return pubFun.returnMsg(201,dateType=dateType,lastWorkDay=lastWorkDay)
    
def searchDay(request):
    data_date = request.GET['date']
    data_empID = request.GET['empID']

    if not pubFun.validate_date(data_date):
        return pubFun.returnMsg(202)
    if not data_empID:
        return pubFun.returnMsg(208,"参数错误，请将当前页面截图后提交给Leader")

    emp = dbfun.searchDB(emp_info,emp_id=data_empID).first()

    day = emp.day_set.filter(date=data_date).first()

    leaveHours = pubFun.searchDayLeave(emp,data_date,[0,1])

    if not day:
        return pubFun.returnMsg(201,hasLeave=(True if leaveHours else False))
        """
        if leaveHours:
            return pubFun.returnMsg(201,hasLeave=True)#msg="当日请假时长:{}".format(leaveHours),
        else:
            return pubFun.returnMsg(201,hasLeave=False)#msg="数据库中没有当天记录,EmpID:{}".format(data_empID),
        """
    else:
        empOT = emp.ot_emp_id.filter(approve__lt=2,date=data_date).first()
        
        return pubFun.returnMsg(201,
            startTimeManual= day.st_om,
            reason=day.reason,
            endTimeOffice=day.et_o,
            startTimeHome=day.st_h,
            endTimeHome=day.et_h,
            workHoursHome=day.wh_h,
            startPath=models.convertPath(day.st_h_path),
            endPath=models.convertPath(day.et_h_path),
            otPath=models.convertPath(day.ot_path),
            workHoursOffice=day.wh,#应该工作的时长
            totalTime=day.wh_o,
            ot=day.wh_ot,
            hasOT=(True if empOT else False),
            hasLeave=(True if leaveHours else False),
            otType=day.ot_type,
            otReason=day.ot_reason,
        )
    """
    return HttpResponse(json.dumps({
        "startTimeManual": day.st_om,
        "reason":day.reason,
        "endTimeOffice":day.et_o,
        "startTime":day.st_h,
        "endTimeHome":day.et_h,
        "workHoursHome":day.wh_h,
        "startPath":day.st_h_path,
        "endPath":day.et_h_path,
        "otPath":day.ot_path,
        "workHoursOffice":day.wh,#应该工作的时长
        "totalTime":day.wh_o,
        "ot":day.wh_ot
        },cls=pubFun.DateEncoder))
    """

def checkDayInfo(request):
    empID = request.GET.get("empID")
    page = request.GET.get('pageNo', 1)
    itemsInPage = request.GET.get('pageSize', 10)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    today = datetime.date.today()
    year = today.year
    month = today.month
    day = today.day
    entryday = emp.EntryDate
    delta180 = datetime.timedelta(days=60)
    delta = datetime.timedelta(days=1)

    begin = today - delta180

    if entryday:
        if begin < entryday:
            begin = entryday
            delta180 = today - begin

    if begin < datetime.date(2021, 1, 1):
        begin = datetime.date(2021,1,1)

    d = begin
    msg = '<span style="color:green;">您在'+str(delta180.days)+'天内的信息记录非常完整</span>'
    st_om = ""
    dayList = []
    while d < today:
        typ, wh = dateInfo(str(d))
        dic = {}
        if wh > 0:
            dayInfo = dbfun.searchDB(db_day,emp_id=emp,date=str(d)).first()
            if not dayInfo:
                whday = 0
                #查leave
            elif not dayInfo.et_o:
                st_om = dayInfo.st_om
                whday = 0
            else:
                st_om = dayInfo.st_om
                whday = dayInfo.wh_o

            #查leave
            days = leave.searchLeave(str(d),emp)[0]
            whday = whday + days * constants.STATUTORY_WORKING_HOURS*60

            #查ot
            ots = ot.searchOT(str(d),emp)
            if ots:
                whday = whday - ots.ot_hours

            if whday < wh*60 -120:
                dic["date"] = str(d)
                dic["startTimeOffice"] = st_om if st_om else "Null"
                if dayInfo:
                    if dayInfo.et_o:
                        dic["endTimeOffice"] = dayInfo.et_o
                    else:
                        dic["endTimeOffice"] = "Null"
                else:
                    dic["endTimeOffice"] = "Null"
                #dic["endTimeOffice"] = dayInfo.et_o if dayInfo.et_o else "Null"
                dic["divwh"] = "{:.1f}小时".format(wh - whday/60)
                dic["leave"] = str(days) + "天" if days else ""
                dic["ot"] = str(ots.ot_hours/60) + "小时" if ots else ""

            st_om = ""
            whday = 0

        if dic:
            dayList.append(dic)

        d += delta

    total = len(dayList)
    #dayList = list(Paginator(dayList, itemsInPage).page(page))
    if dayList:
        msg = '<span style="color:red;">在过去的'+str(delta180.days)+'天中，您有如下日期的信息不完整，请根据实际情况填写。如有需要，请联系组长。</span>'

    return pubFun.returnMsg(220,m=msg,total=total,pageSize=int(itemsInPage),pageNo=int(page),data=dayList)
