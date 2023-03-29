import json,datetime,calendar
from . import dbfun,pubFun,constants,ot,day,account,search,compoff as compoffModel
from dbModel.models import leave,day as dayModel
from dbModel.models import emp_info
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

def leave_cancel(request):
    leaveID = request.GET['id']
    empID = request.GET['empID']

    msg = ot.cancel_apply(leave,leaveID,empID,"请假")

    msg = msg if msg else "取消成功"

    return pubFun.returnMsg(200, msg)

def search_leave_days(request):#GET
    startDate = request.GET['date']
    endDate = request.GET['date_end']
    startDuration = request.GET.get('startDuration',0)
    endDuration = request.GET.get('endDuration', 0)
    empID = request.GET.get('empID',"")

    pubFun.paraValidate(empID=empID)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    totalHours = 0
    dateTemp = endDate
    while startDate == pubFun.compareDate(startDate,dateTemp)[0]:
        totalHours += constants.STATUTORY_WORKING_HOURS
        dateTemp = day.dateInfo(dateTemp,needLastDay=True,emp=emp)[2]

    if startDuration == 2:#下半天开始
        totalHours = totalHours - 4
    if endDuration == 1:#上半天结束
        totalHours = totalHours - 4

    return pubFun.returnMsg(201, leaveDays=(totalHours/8))

def searchLeaveM(year,month,emp=None,empID=""):
    """
    查找当月的请假总时长
    """
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    days = calendar.monthrange(year,month)[1]
    total = 0
    for d in range(1,days+1):
        dayV = str(year) + "-" + str(month) + "-" + str(d)
        total += searchLeave(dayV,emp)[0]
    return total

def searchLeaveMList(year,month,emp=None,empID="",returnType=1):
    """
    查询当月全部请假
    returnType=1:按天返回 用于计算
    returnType=2：按月返回 用于显示
    """
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    days = calendar.monthrange(year,month)[1]
    leaves = []
    if returnType==1:
        for d in range(1,days+1):
            dayV = str(year) + "-" + str(month) + "-" + str(d)
            leave_ = searchLeaveList(dayV,emp)
            if leave_:
                leaves.append(leave_)
    elif returnType == 2:
        leaves.append(dbfun.searchDB(leave, emp_id=emp, date__year=year, date__month=month))
    return leaves

def searchLeave(date,emp=None,empID=""):
    #根据日期查询是否有请假
    #返回当前日期请假的时长，以天为单位
    days = 0
    typ = 0
    items = searchLeaveList(date,emp,empID)
    
    if not items:
        return days,0
    else:
        for item in items:
            if pubFun.compareDate(str(item.date),date)[2] ==0:
            #if item.date == date:
                if item.start_duration != 0:
                    days += 0.5
                    typ = item.start_duration
                else:
                    days += 1
            elif pubFun.compareDate(str(item.date_end),date)[2] ==0:
            #elif item.date_end == date:
                if item.end_duration != 0:
                    days += 0.5
                    typ = item.end_duration
                else:
                    days += 1
            else:
                days = 1

    return days ,typ

def searchLeaveList(date,emp=None,empID=""):
    #根据日期查询 当日的请假
    #返回当日的请假list
    if day.dateInfo(date,emp=emp)[1] == 0:
        return None
    
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    return emp.leave_set.filter(date__lte=date,date_end__gte=date,approve__lt=2)

@csrf_exempt
def leave_apply(request):
    json_result = json.loads(request.body)

    date = json_result['date']
    endDate = json_result['date_end']
    empID = json_result['empID']
    leaveType = json_result['leaveType']
    leaveDays = json_result['leaveDays']#以天为单位，程序写好了，不好改了
    reason = json_result['reason']

    if "ultimatixNo" in json_result:
        leaveNo = json_result['ultimatixNo']
    else:
        leaveNo = None

    if 'startDuration' in json_result:
        startDuration = json_result['startDuration']
        if not startDuration:
            startDuration = 0
    else:
        startDuration = 0

    if 'endDuration' in json_result:
        endDuration = json_result['endDuration']
        if not endDuration:
            endDuration = 0
    else:
        endDuration = 0

    if 'approve' in json_result: # 用于取消和批准请假
        approve = json_result['approve']
    else:
        approve = 0

    #查找当前人，当前天的请假总时长，大于8返回不可以
    #如果同一时间段，不可以
    #请假不可以更新，要先取消，再新增
    
    msg = ""

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    
    #开始，结束的日期都应该是平日
    if day.dateInfo(date,emp=emp)[1] == 0 or day.dateInfo(endDate,emp=emp)[1] == 0 :
        msg = "Emp:{},您申请中的开始或结束日期不是工作日".format(empID)
        return pubFun.returnMsg(208,msg)

    daydiv = datetime.timedelta(days=1)
    d = datetime.date.fromisoformat(date)
    dE = datetime.date.fromisoformat(endDate)

    while d<=dE:
        days,duration = searchLeave(d.isoformat(),emp=emp)
        if days == 1:
            msg = "Emp:{},您申请的时间段包含其他请假".format(empID)
        elif days > 0:
            if d == datetime.date.fromisoformat(date):
                if startDuration == duration:
                    msg = "Emp:{},您申请的时间段包含其他请假".format(empID)
            elif d == dE:
                if endDuration == duration:
                    msg = "Emp:{},您申请的时间段包含其他请假".format(empID)
            else:
                msg = "Emp:{},您申请的时间段包含其他请假".format(empID)
        else:
            pass
        if msg:
            return pubFun.returnMsg(208,msg)
        d += daydiv

    leaveRestDict = search.searchAccount(emp)[1]
    #print(leaveType,leaveRestDict["compoffNew"],leaveDays,leaveDays * constants.STATUTORY_WORKING_HOURS * 60)
    if leaveType == 3:#病假
        #print(leaveDays,leaveRestDict["sickLeave"])
        if leaveDays > leaveRestDict["sickLeave"]:
            msg = "Emp:{},您申请的时长已经超过可用天数：{}天".format(empID,leaveRestDict["statAnnualLeave"])
    elif leaveRestDict["statAnnualLeave"] > 0 and leaveType != 4:
        if leaveType in [2] or leaveDays > leaveRestDict["statAnnualLeave"]:
            msg = "Emp:{},请优先使用您的法定年假，且不要超过{}天".format(empID,leaveRestDict["statAnnualLeave"])
    elif leaveType == 1 and leaveRestDict["statAnnualLeave"] == 0:
        msg = "Emp:{},您没有可以使用的法定年假".format(empID)
    elif leaveRestDict["compoff"] >= (constants.STATUTORY_WORKING_HOURS/2):
        if leaveType in [2] or leaveDays * constants.STATUTORY_WORKING_HOURS > leaveRestDict["compoff"]:
            pass
            #msg = "Emp:{},请优先使用您的倒休假期，且不要超过{}".format(empID,pubFun.convertHoursWithPoint(leaveRestDict["compoff"]))
    elif leaveType == 4 and leaveRestDict["compoffNew"] < leaveDays * constants.STATUTORY_WORKING_HOURS * 60:
        #这个倒休的leaveDays单位要改，改成分钟。最小单位为30分钟 -- 应该是搞定了8-24
        msg = "Emp:{},您没有足够的可以使用的倒休假期".format(empID)
    elif leaveType == 2 and leaveRestDict["beneAnnualLeave"] == 0:
        msg = "Emp:{},您没有可以使用的福利年假".format(empID)

    if msg:
        return pubFun.returnMsg(208,msg)

    if leaveType == 4:
        #计算倒休的compoff_from(列表)
        #倒休的提交时间单位为小时
        compoff_from = compoffModel.useCompoffAccount(emp,leaveDays*constants.STATUTORY_WORKING_HOURS)
    else:
        compoff_from = account.useLeaveAccount(emp,wh=-leaveDays,leaveType=leaveType,leaveRestDict=leaveRestDict,compoff=[])

    d = datetime.datetime.now()
    compoff_from.append("date:"+str(d.year)+"-"+str(d.month))

    dbfun.addDB(leave,emp=emp,emp_id=emp,date=date,date_end=endDate,leave_type=leaveType,\
                leave_days=leaveDays,reason=reason,start_duration=startDuration,\
                end_duration=endDuration,leave_from=compoff_from,approve=approve,levNo=leaveNo)
    msg = "申请成功，请通知Leader审批"
    
    return pubFun.returnMsg(200,msg)

def leave_approve(request):
    leaveID = request.GET['id']
    empID = request.GET['empID']

    msg = ot.approve_apply(leave,leaveID,empID,"请假")

    if "审批成功" in msg:
        return pubFun.returnMsg(200, msg)
    else:
        return pubFun.returnMsg(208, msg)

def leaveDayAndWH(item=None,id=None):
    """
    参数：id：leave的id
    返回：
    1、集合，日期和当天的时长(小时)
    2、当前月的总时长(小时)
    3、非当前月的总时长(小时)
    """
    if not item:
        if id:
            item = dbfun.searchDB(leave,id=id).first()
        else:
            return {}

    startDate = item.date
    endDate = item.date_end

    date_format = "%Y-%m-%d"

    # if startDate == endDate:
    #     if item.start_duration >0:
    #         return {datetime.datetime.strftime(startDate,date_format):constants.STATUTORY_WORKING_HOURS/2}

    #sd = datetime.datetime.strptime(startDate, date_format)
    #ed = datetime.datetime.strptime(endDate, date_format)

    delta = datetime.timedelta(days=1)

    interval = int((endDate - startDate).days)

    result = {}
    currentMonthWH = 0
    preMonthWH = 0

    now = datetime.datetime.now()

    for i in range(0, interval + 1, 1):
        date = startDate+delta*i
        d = datetime.datetime.strftime(date,date_format)
        dateType, workHours = day.dateInfo(d)
        if dateType == 1 or (dateType==4 and workHours > 0):
            #平日或者工作时间>0的特殊日期才会有请假
            if i == 0:
                if item.start_duration > 0:
                    result[d] = constants.STATUTORY_WORKING_HOURS/2
                else:
                    result[d] = constants.STATUTORY_WORKING_HOURS
            elif i == interval:
                if item.end_duration > 0:
                    result[d] = constants.STATUTORY_WORKING_HOURS/2
                else:
                    result[d] = constants.STATUTORY_WORKING_HOURS
            else:
                result[d] = constants.STATUTORY_WORKING_HOURS

            if date.month == now.month:
                dayInfo = dbfun.searchDB(dayModel,emp_id=item.emp_id,date=d).first()
                if dayInfo:
                    if dayInfo.st_om and dayInfo.et_o:
                        currentMonthWH += result[d]
            else:
                preMonthWH += result[d]

    return result,currentMonthWH,preMonthWH