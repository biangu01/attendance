from . import dbfun,pubFun,day,account,leave,compoff
from dbModel.models import emp_info, ot, otTypeDict
from django.db.models import Q
from django.views.decorators.csrf import csrf_exempt
import json,re,datetime

@csrf_exempt
def ot_apply(request):
    date = request.POST['date']
    empID = request.POST['empID']
    startTime = request.POST['startTime']
    endTime = request.POST['endTime']
    #reason = request.POST['reason']

    reason = request.POST.get("reason",default="")
    
    otType = request.POST['otType']
    #weekday = request.POST['weekday']
    otHours = request.POST['otHours']
    otHours = float(otHours) * 60 #转换成分钟

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    dateType,workHours = day.dateInfo(date,emp=emp)

    #平日ot结束时间应该早于当日下班时间
    if workHours >0:
        day_endTime = emp.day_set.filter(date=date).first().et_o
        if not day_endTime:
            return pubFun.returnMsg(208,message="没找到当天工作信息")
        else:
            day_endTime = str(day_endTime)
            early, later, div = pubFun.compareTime(endTime,day_endTime)
            if div != 0:
                if endTime == later:
                    pass
                    #return pubFun.returnMsg(208,message="结束时间应早于当日下班时间" + day_endTime)

    #是否要扣掉加班
    
    onl = request.POST['onl']

    meelFee = request.POST.get("meelFee",default=0)

    taxiFee = request.POST.get("taxiFee",default=0)

    otRequestDate = request.POST.get('otRequestDate',default=None)
    
    otRequestTime = request.POST.get('otRequestTime',default=None)

    otID = request.POST.get("id",default=None)

    approve = request.POST.get("approve",default=0)

    weekday = dateType

    if otID and approve == 2:
        ot_ = dbfun.searchDB(ot,id=otID,emp_id=empID,date=date).first()
        if ot_.approve == 1:#app
            msg = "Emp:{},此条加班已经被审批，如需取消，请联系您的Leader".format(empID)
            return pubFun.returnMsg(208, msg)
        else:
            app = ot_.approve
            ot_.approve = 2
            dbfun.updateDB(ot_,dicOri={"approve":app},dicNew={"approve":2})
            msg = "您的加班已取消"
            return pubFun.returnMsg(200,msg)

    name_pinyin = pubFun.convertNamePinyin(emp.name_pinyin)

    otPath = ""
    
    if request.FILES.get("otRequest",default=None):
        otImg = request.FILES['otRequest']
        otPath = pubFun.saveImg(otImg, empID,name_pinyin, date, "otRequestOffice")

    ot_ = ot.objects.filter(Q(emp_id=empID,date=date)&~Q(approve=2)).first()

    if ot_ and ot_.approve == 1:
        msg = "Emp:{},当日已有被审批的加班，如需取消，请联系您的Leader".format(empID)
    elif ot_ and ot_.approve == 0:
        dicOri = {}
        dicNew = {}
        ot_.start_time = pubFun.compUpdate(dicOri,dicNew,"startTime",ot_.start_time,startTime)
        ot_.end_time = pubFun.compUpdate(dicOri,dicNew,"endTime",ot_.end_time,endTime)
        ot_.reason = pubFun.compUpdate(dicOri,dicNew,"reason",ot_.reason,reason)
        ot_.ot_type = pubFun.compUpdate(dicOri,dicNew,"otType",ot_.ot_type,otType)
        ot_.weekday = pubFun.compUpdate(dicOri,dicNew,"weekday",ot_.weekday,weekday)
        ot_.ot_hours = pubFun.compUpdate(dicOri,dicNew,"otHours",ot_.ot_hours,otHours)
        ot_.onl = pubFun.compUpdate(dicOri,dicNew,"onl",ot_.onl,onl)
        ot_.meel_fee = pubFun.compUpdate(dicOri,dicNew,"meelFee",ot_.meel_fee,meelFee)
        ot_.taxi_fee = pubFun.compUpdate(dicOri,dicNew,"taxiFee",ot_.taxi_fee,taxiFee)
        ot_.ot_request_date = pubFun.compUpdate(dicOri,dicNew,"otRequestDate",ot_.ot_request_date,otRequestDate)
        ot_.ot_request_time = pubFun.compUpdate(dicOri,dicNew,"otRequestTime",ot_.ot_request_time,otRequestTime)
        ot_.ot_path = pubFun.compUpdate(dicOri,dicNew,"otPath",ot_.ot_path,otPath)
        ot_.approve = pubFun.compUpdate(dicOri,dicNew,"approve",ot_.approve,approve)
        dbfun.updateDB(ot_,dicOri=dicOri,dicNew=dicNew)
        msg = "更新成功"
    else:
        #print(otPath,len(otPath),type(otPath))
        dbfun.addDB(ot,emp=emp,emp_id=emp,date=date,start_time=startTime,end_time=endTime,reason=reason,
                    ot_type=otType,weekday=weekday,ot_hours=otHours,onl=onl,meel_fee=meelFee,
                    taxi_fee=taxiFee,ot_request_date=otRequestDate,ot_request_time=otRequestTime,
                    ot_path=otPath,approve=approve)
        msg = "添加成功"
    
    return pubFun.returnMsg(200,message=msg)

def addOTInfo(empID,otHours,date,startTime,endTime,reason,otType,onl,meelFee,taxiFee,approve):
    emp = dbfun.searchDB(emp_info, emp_id=empID).first()
    otHours = float(otHours) * 60  # 转换成分钟
    dateType, workHours = day.dateInfo(date, emp=emp)
    weekday = dateType

    ot_ = ot.objects.filter(emp_id=empID, date=date).first()

    if not meelFee or meelFee == "nan":
        meelFee = 0
    if not taxiFee or taxiFee == "nan":
        taxiFee = 0

    if ot_:
        dicOri = {}
        dicNew = {}
        ot_.start_time = pubFun.compUpdate(dicOri,dicNew,"startTime",ot_.start_time,startTime)
        ot_.end_time = pubFun.compUpdate(dicOri,dicNew,"endTime",ot_.end_time,endTime)
        ot_.reason = pubFun.compUpdate(dicOri,dicNew,"reason",ot_.reason,reason)
        ot_.ot_type = pubFun.compUpdate(dicOri,dicNew,"otType",ot_.ot_type,otType)
        ot_.weekday = pubFun.compUpdate(dicOri,dicNew,"weekday",ot_.weekday,weekday)
        ot_.ot_hours = pubFun.compUpdate(dicOri,dicNew,"otHours",ot_.ot_hours,otHours)
        ot_.onl = pubFun.compUpdate(dicOri,dicNew,"onl",ot_.onl,onl)
        ot_.meel_fee = pubFun.compUpdate(dicOri,dicNew,"meelFee",ot_.meel_fee,meelFee)
        ot_.taxi_fee = pubFun.compUpdate(dicOri,dicNew,"taxiFee",ot_.taxi_fee,taxiFee)
        ot_.approve = pubFun.compUpdate(dicOri,dicNew,"approve",ot_.approve,approve)
        dbfun.updateDB(ot_,dicOri=dicOri,dicNew=dicNew)
        msg = "更新成功"
    else:
        #print(otPath,len(otPath),type(otPath))
        dbfun.addDB(ot,emp_id=emp,date=date,start_time=startTime,end_time=endTime,reason=reason,
                    ot_type=otType,weekday=weekday,ot_hours=otHours,onl=onl,meel_fee=meelFee,
                    taxi_fee=taxiFee,approve=approve)
        msg = "添加成功"
    return msg


def ot_cancel(request):
    otID = request.GET['id']
    empID = request.GET['empID']

    msg = cancel_apply(ot,otID,empID,"加班")

    # 取消倒休
    ot_ = dbfun.searchDB(ot, id=otID).first()
    emp = dbfun.searchDB(emp_info, emp_id=empID).first()
    compoff.recordCompoff(emp=ot_.emp_id, date=str(ot_.date), office=True, wh=ot_.ot_hours, approve=4, status=5,empop=emp)

    return pubFun.returnMsg(200, msg)


def cancel_apply(db,itemID,empID,msg):
    
    item = dbfun.searchDB(db,id=itemID).first()

    message = ""

    if item.emp_id.emp_id == empID:#员工本人
        if item.approve == 1:
            message = "Emp:{},此条".format(empID) + msg + "已经被审批，如需取消，请联系您的Leader"
        elif item.approve == 2:
            message = "Emp:{},操作失败：此条".format(empID) + msg + "已经为取消状态"
        else:
            app = item.approve
            item.approve = 2
            dbfun.updateDB(item,dicOri={"approve":app},dicNew={"approve":2})
            message = "您的"+ msg +"已取消"
            if msg == "加班":
                # 本人取消ot，不影响account账户
                pass
            elif msg == "请假":
                if item.leave_type == 4:
                    message = compoff.cancelCompoff(item.leave_from)
                else:
                    message = account.useLeaveAccount(item.emp_id, wh=item.leave_days,compoff=item.leave_from)
        return message
    else:#Leader操作
        #批了就不能取消了。。
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()
        if item.approve != 2:
            app = item.approve
            item.approve = 2
            dbfun.updateDB(item, dicOri={"approve": app}, dicNew={"approve": 2},emp=emp)
            # 取消account中的数
            if msg == "加班":
                if item.approve == 1:
                    message += str(account.saveAccountOT(item.emp_id, item.date, item.ot_hours, 0, office=True, apply=False, out=True))
                    message += " "
                    message += str(account.saveAccountOT(item.emp_id, item.date, 0, item.ot_hours, office=True, apply=True, out=False))
            elif msg == "请假":
                if item.leave_type == 4:
                    message = compoff.cancelCompoff(item.leave_from)
                else:
                    message = account.useLeaveAccount(item.emp_id, wh=item.leave_days, compoff=item.leave_from)
            #message = "本条" + msg + "已取消"
        else:
            message = "操作失败：本条" + msg + "已经为取消状态"

        return message

def ot_approve(request):
    otID = request.GET['id']
    empID = request.GET['empID']

    msg = approve_apply(ot,otID,empID,"加班")

    if "审批成功" in msg:
        #添加倒休
        ot_ = dbfun.searchDB(ot,id=otID).first()
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()
        compoff.recordCompoff(emp=ot_.emp_id,date=str(ot_.date),office=True,wh=ot_.ot_hours,approve=1,status=4,empop=emp)
        return pubFun.returnMsg(200, msg)
    else:
        return pubFun.returnMsg(208, msg)

def approve_apply(db,itemID,empID,msg):#Leader的操作
    item = dbfun.searchDB(db, id=itemID).first()
    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    message = ""

    if item.approve == 0:
        app = item.approve
        item.approve = 1
        # 增加account中的数
        if msg == "加班":
            #将时间放入pay的账户
            message += "审批成功 "
            message += str(account.saveAccountOT(item.emp_id, item.date, 0, item.ot_hours, office=True, apply=True, out=False))
            #将时间从compoff或pay we_ot账户取出
            message += str(account.saveAccountOT(item.emp_id, item.date, item.ot_hours, 0, office=True, apply=False, out=True))
        elif msg == "请假":
            message = "审批成功 "
            #这里应该把compoff account 在公司平日倒休 compoff_office_wd 补齐
            a,currentMonthWH,preMonthWH = leave.leaveDayAndWH(item=item)
            if currentMonthWH > 0:
                date = list(a.keys())[-1]
                message += str(account.saveAccountOT(item.emp_id, date, 0, currentMonthWH*60, office=True, apply=False, out=False))
            if preMonthWH > 0:
                message += "请假时长{}小时已过期，无法返还 ".format(preMonthWH)
            pass
        dbfun.updateDB(item, dicOri={"approve": app}, dicNew={"approve": 1}, emp=emp)
    elif item.approve == 1:
        message = "操作失败：本条" + msg + "已经为批准状态"
    else:
        message = "操作失败：本条" + msg + "已经为取消状态"

    return message

def otType(request):
    empID = request.GET['empID']

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    groups = dbfun.findGroupIDforEmp(emp)

    dic = {}

    for group in groups:
        groupname = group.name.lower()
        for s in otTypeDict.keys():
            if groupname.startswith(s):
                dic.update(otTypeDict[s])
    if not dic:
        dic.update(otTypeDict["other"])

    return pubFun.returnMsg(201, data=dic)

def findOT(request):
    date = request.GET.get("date","")
    empID = request.GET.get("empID","")

    pubFun.paraValidate(date=date,empID=empID)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    ot_ = searchOT(date,emp)#dbfun.searchDB(ot,emp_id=emp,date=date,approve__lt=2).first()

    if ot_:
        data = ot_.viewData()
        data = data.replace("\\",r"\\")
        data = re.sub("[\s+]","",data)
        return pubFun.returnMsg(201,data=json.loads("{" + data + "}"))
    else:
        return pubFun.returnMsg(201)

    
def searchOT(date,emp=None,empID=""):
    if empID:
        emp = dbfun.searchDB(emp_info, emp_id=empID).first()

    return dbfun.searchDB(ot, emp_id=emp, date=date, approve__lt=2).first()
