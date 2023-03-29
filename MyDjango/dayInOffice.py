import json,time,datetime
from . import pubFun,day,dbfun,constants,account,compoff
from django.views.decorators.csrf import csrf_exempt
from dbModel.models import day as db_day
from dbModel.models import emp_info

def dayTimeInOffice(date,sts,stm,et,wh,dt):
    """
    date - 上班日期
    sts - 上班时间-系统
    stm - 上班时间-手动
    et - 下半时间
    wh - 应该工作时长

    返回 总工作时长，超出法定工作时长的所有时间即可提加班时长 (分钟)

    存数据库的时候要改一下，要记录一个当日的结余
    """
    st = pubFun.compareTime(sts if sts else stm,stm)[0]

    #去掉秒
    arr = st.split(":")
    if len(arr) > 2 :
        arr = arr[:-1]
        st = ":".join(arr)

    if pubFun.compareTime(st,"09:00")[0] == st and day.dateInfo(date)[1] > 0:
        st = "09:00"
    
    dateformat = "%Y-%m-%d %H:%M"

    #午休的开始结束时间
    if wh > 0 :#按工作日算
        break_start = time.strptime(date + " " + constants.WORKING_DAY_BREAK_START,dateformat)
        break_end = time.strptime(date + " " + constants.WORKING_DAY_BREAK_END_NODE,dateformat)
    else:
        break_start = time.strptime(date + " " + constants.WEEKEND_BREAK_START,dateformat)
        break_end = time.strptime(date + " " + constants.WEEKEND_BREAK_END,dateformat)

    #将上下班时间转换为时间戳，方便计算
    st_office = time.strptime(date + " " + st,dateformat)
    et_office = time.strptime(date + " " + et,dateformat)

    #要减去所有午休的时间
    """
    if break_start < st_office < break_end:
        st_office = break_end
    if break_start < et_office < break_end:
        et_office = break_start
    """
    
    #一天总工作时长
    #totalTime = pubFun.compareTime(st,et)[2]
    totalTime = (time.mktime(et_office)-time.mktime(st_office))/60

    if et_office < st_office:
        totalTime = 24 * 60 + totalTime
    
    #如果上下班时间跨越午休，则减去一小时
    if (st_office <= break_start and et_office >= break_end) \
    or (et_office <= st_office <= break_start) :#正常的情况，需要减1 or 隔夜
        totalTime = totalTime - 60

    #if break_start < et_office < break_end

    #超出应工作时长部分s
    """
    if wh > 0 :
        over_part = totalTime - wh*60
    else:
        over_part = totalTime
    """

    #超出应工作时长部分
    if dt == 4:#特殊日期
        otSt = totalTime - constants.STATUTORY_WORKING_HOURS * 60
        if otSt > 0:
            ot = otSt
        else:
            #工作日调休为休息日
            ot = totalTime - wh * 60
            #休息日调休为工作日
            if wh >0:
                ot = 0 if ot>0 else ot
    else:
        ot = totalTime - wh * 60
    """
    if wh > 0 :
        ot = totalTime - (wh if wh != constants.STATUTORY_WORKING_HOURS else constants.STATUTORY_WORKING_HOURS)*60
    else:
        ot = totalTime
    """
    
    return totalTime, ot

@csrf_exempt
def day_office(request):
    #POST - in office
    json_result = json.loads(request.body)

    date = json_result['date']
    empID = json_result['empID']
    stman = json_result['startTimeManual']
    stsys = json_result['startTimeSystem']

    et = None
    if "endTime" in json_result:
        et = json_result['endTime']

    reason = ""
    if "reason" in json_result:
        reason = json_result['reason']

    ott = None
    if "otType" in json_result:
        ott = json_result['otType']

    otReason = ""
    if "otReason" in json_result:
        otReason = json_result['otReason']

    if ott:
        if ott<3:
            otReason = ""

    now = datetime.datetime.now()
    today = pubFun.compareDate(date,str(now.year) + "-" + str(now.month) + "-" + str(now.day))[2] == 0

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    day_ = emp.day_set.filter(date=date).first()

    dateType, workHours = day.dateInfo(date,emp=emp)
    
    if day_:
        reason = day_.reason if day_.reason else reason
        if today:
            stsys = day_.st_os if day_.st_os else stsys
            if et:
                totalTime, ot = dayTimeInOffice(date,str(stsys),stman,et,workHours,dateType)
        else:
            stsys = day_.st_os if day_.st_os else None
            if et:
                totalTime, ot = dayTimeInOffice(date,stman,stman,et,workHours,dateType)
    else:
        if not today:
            stsys = None
            reason = "系统补填:" + str(now.year) + "-" + str(now.month) + "-" + str(now.day)
        if et:
            totalTime, ot = dayTimeInOffice(date,stman,stman,et,workHours,dateType)

    #存数据库
    #ot为分钟
    if day_:
        #更新
        dicOri = {}
        dicNew = {}
        if et:
            day_.st_om = pubFun.compUpdate(dicOri,dicNew,"startTimeManual",day_.st_om,stman)
            day_.st_os = pubFun.compUpdate(dicOri,dicNew,"startTimeSystem",day_.st_os,stsys)
            day_.reason = pubFun.compUpdate(dicOri,dicNew,"reason",day_.reason,reason)
            day_.et_o = pubFun.compUpdate(dicOri,dicNew,"endTimeOffice",day_.et_o,et)
            day_.wh = pubFun.compUpdate(dicOri,dicNew,"workHours",day_.wh,workHours)
            day_.wh_o = pubFun.compUpdate(dicOri,dicNew,"workHoursInOffice",day_.wh_o,totalTime)
            account.saveAccountOT(emp, date, day_.wh_ot, ot, office=True, apply=False,out=False)
            day_.wh_ot = pubFun.compUpdate(dicOri,dicNew,"workHoursOT",day_.wh_ot,ot)
            if ott:
                day_.ot_type = pubFun.compUpdate(dicOri,dicNew,"otType",day_.ot_type,ott)
            if otReason or otReason == "":
                day_.ot_reason = pubFun.compUpdate(dicOri,dicNew,"otReason",day_.ot_reason,otReason)
        else:
            day_.st_om = pubFun.compUpdate(dicOri,dicNew,"startTimeManual",day_.st_om,stman)
            day_.st_os = pubFun.compUpdate(dicOri,dicNew,"startTimeSystem",day_.st_os,stsys)
            day_.reason = pubFun.compUpdate(dicOri,dicNew,"reason",day_.reason,reason)
            day_.wh = pubFun.compUpdate(dicOri,dicNew,"workHours",day_.wh,workHours)
        dbfun.updateDB(day_,dicOri=dicOri,dicNew=dicNew)
        msg = "更新成功"
        #dbfun.updateDB(day_,st_om=stman,st_os=stsys,reason=reason,et_o=et,wh=workHours,wh_o=totalTime,wh_ot=ot)
    else:
        if et:
            if not ott:
                ott = 1
            dbfun.addDB(db_day,emp=emp,emp_id=emp,date=date,st_om=stman,st_os=stsys,
                        reason=reason,et_o=et,wh=workHours,wh_o=totalTime,wh_ot=ot,ot_type=ott,ot_reason=otReason)
            account.saveAccountOT(emp, date, 0, ot, office=True, apply=False,out=False)
        else:
            dbfun.addDB(db_day,emp=emp,emp_id=emp,date=date,st_om=stman,st_os=stsys,
                        reason=reason,wh=workHours)
        msg = "添加成功"

    if dateType == 3:#节假日
        compoff.recordCompoff(emp=emp, date=date, office=True,wh=workHours, approve=0, status=4)

    if et:
        return pubFun.returnMsg(201,totalTime=totalTime,ot=ot,msg=msg)
    else:
        return pubFun.returnMsg(201,msg=msg)


def addDayInfo(date,empID,stman,et,reason,st_h,et_h,wh_h):
    """
    用于补1-3月的信息。4_30。
    一般用不上
    """
    emp = dbfun.searchDB(emp_info, emp_id=empID).first()
    day_ = emp.day_set.filter(date=date).first()

    dateType, workHours = day.dateInfo(date, emp=emp)
    totalTime = 0
    ot = 0
    stsys = None

    if day_:
        reason = day_.reason if day_.reason else reason
        stsys = day_.st_os if day_.st_os else None
        if et:
            totalTime, ot = dayTimeInOffice(date, stman, stman, et, workHours, dateType)
    else:
        now = datetime.datetime.now()
        reason = "系统补填:" + str(now.year) + "-" + str(now.month) + "-" + str(now.day)
        if et:
            totalTime, ot = dayTimeInOffice(date, stman, stman, et, workHours, dateType)

    # 存数据库
    if day_:
        # 更新
        dicOri = {}
        dicNew = {}
        if et:
            day_.st_om = pubFun.compUpdate(dicOri, dicNew, "startTimeManual", day_.st_om, stman)
            day_.st_os = pubFun.compUpdate(dicOri, dicNew, "startTimeSystem", day_.st_os, stsys)
            day_.reason = pubFun.compUpdate(dicOri, dicNew, "reason", day_.reason, reason)
            day_.et_o = pubFun.compUpdate(dicOri, dicNew, "endTimeOffice", day_.et_o, et)
            day_.wh = pubFun.compUpdate(dicOri, dicNew, "workHours", day_.wh, workHours)
            day_.wh_o = pubFun.compUpdate(dicOri, dicNew, "workHoursInOffice", day_.wh_o, totalTime)
            account.saveAccountOT(emp, date, day_.wh_ot, ot, office=True, apply=False, out=False)
            day_.wh_ot = pubFun.compUpdate(dicOri, dicNew, "workHoursOT", day_.wh_ot, ot)

        else:
            day_.st_om = pubFun.compUpdate(dicOri, dicNew, "startTimeManual", day_.st_om, stman)
            day_.st_os = pubFun.compUpdate(dicOri, dicNew, "startTimeSystem", day_.st_os, stsys)
            day_.reason = pubFun.compUpdate(dicOri, dicNew, "reason", day_.reason, reason)
            day_.wh = pubFun.compUpdate(dicOri, dicNew, "workHours", day_.wh, workHours)
        if st_h or et_h or wh_h:
            day_.st_h = pubFun.compUpdate(dicOri, dicNew, "startTimeHome", day_.st_h, st_h)
            day_.et_h = pubFun.compUpdate(dicOri, dicNew, "endTimeHome", day_.et_h, et_h)
            account.saveAccountOT(emp, date, day_.wh_h, wh_h, office=False, apply=False, out=False)
            day_.wh_h = pubFun.compUpdate(dicOri, dicNew, "workHoursAtHome", day_.wh_h, wh_h)
        dbfun.updateDB(day_, dicOri=dicOri, dicNew=dicNew)
        msg = "更新成功"
        # dbfun.updateDB(day_,st_om=stman,st_os=stsys,reason=reason,et_o=et,wh=workHours,wh_o=totalTime,wh_ot=ot)
    else:
        dbfun.addDB(db_day, emp=emp, emp_id=emp, date=date, st_om=stman, st_os=stsys,reason=reason, et_o=et,
                    wh=workHours, wh_o=totalTime, wh_ot=ot,st_h=st_h,et_h=et_h,wh_h=wh_h)
        account.saveAccountOT(emp, date, 0, ot, office=True, apply=False, out=False)
        msg = "添加成功"

    return msg
