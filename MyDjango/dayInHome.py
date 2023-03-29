import json
from . import dbfun,pubFun,account,day,dayInOffice,compoff
from dbModel.models import day as db_day
from dbModel.models import emp_info
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def day_home(request):
    """
    json_result = json.loads(request.body)

    date = json_result['date']
    empID = json_result['empID']
    st = json_result['startTime']
    wh = json_result['workHours']
    
    et = json_result['endTime']
    startImg = json_result['startImg']
    endImg = json_result['endImg']
    """
    date = request.POST['date']
    empID = request.POST['empID']
    st = request.POST['startTime']
    wh = request.POST['workHours']
    wh = int(wh)

    et = request.POST['endTime']

    #将wh计入平日compoff_home_wd或周末compoff_home1
    """
    先拿到本表当前的数据，如果没有或0，则为新增，直接+，存account
    否则，用新的-旧的，差存到account, =0不做处理
    """

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    dateType,workHours = day.dateInfo(date,emp=emp)

    #平日在家开始的时间应该晚于19点且晚于当日下班时间
    if workHours >0:
        if st != "19:00":
            if st == pubFun.compareTime(st,"19:00")[0]:
                return pubFun.returnMsg(208,message="开始时间应等于或晚于19:00")
        day_endTime = emp.day_set.filter(date=date).first()
        if day_endTime:
            day_endTime = str(day_endTime.et_o)
            if st == pubFun.compareTime(st,day_endTime)[0]:
                return pubFun.returnMsg(208,message="开始时间应晚于当日下班时间" + day_endTime)

    minute = dayInOffice.dayTimeInOffice(date,st,st,et,0,1)[0]
    #工作时长应小于或等于填写的开始和结束时间
    if wh > minute:
        return pubFun.returnMsg(208,message="您的工作时间应小于或等于" + str(int(minute)) + "分钟")
    
    name_pinyin = pubFun.convertNamePinyin(emp.name_pinyin)

    if "startImg" in request.FILES:
        startImg = request.FILES['startImg']
        startPath = pubFun.saveImg(startImg, empID, name_pinyin, date, "startTimeHome")
    else:
        startImg = request.POST['startImg']
        startPath = startImg

    if "endImg" in request.FILES:
        endImg = request.FILES['endImg']
        endPath = pubFun.saveImg(endImg, empID, name_pinyin, date, "endTimeHome")
    else:
        endImg = request.POST['endImg']
        endPath = endImg

    otPath = ""

    if "otImg" in request.FILES:
        if request.FILES.get("otImg", default=None):  # has_key('otImg'):
            otImg = request.FILES['otImg']
            otPath = pubFun.saveImg(otImg, empID, name_pinyin, date, "otRequestHome")
    else:
        otPath = request.POST.get("otImg", "")

    #day_ = dbfun.searchDB(db_day,date=date,emp_id=empID).first()
    day_ = emp.day_set.filter(date=date).first()
    
    if day_:
        #更新
        dicOri = {}
        dicNew = {}
        day_.st_h = pubFun.compUpdate(dicOri,dicNew,"startTimeHome",day_.st_h,st)
        day_.et_h = pubFun.compUpdate(dicOri,dicNew,"endTimeHome",day_.et_h,et)
        account.saveAccountOT(emp, date, day_.wh_h, wh, office=False, apply=False,out=False)
        day_.wh_h = pubFun.compUpdate(dicOri,dicNew,"workHoursAtHome",day_.wh_h,wh)
        day_.st_h_path = pubFun.compUpdate(dicOri,dicNew,"startImage",day_.st_h_path,startPath)
        day_.et_h_path = pubFun.compUpdate(dicOri,dicNew,"endImage",day_.et_h_path,endPath)
        day_.ot_path = pubFun.compUpdate(dicOri,dicNew,"otImage",day_.ot_path,otPath)
        dbfun.updateDB(day_,dicOri=dicOri,dicNew=dicNew)
        msg = "更新成功"
    else:
        dbfun.addDB(db_day,emp=emp,
                emp_id=emp,date=date,st_h=st,et_h=et,
                wh_h=wh,st_h_path=startPath,et_h_path=endPath,ot_path=otPath,wh=0)
        account.saveAccountOT(emp, date, 0, wh, office=False, apply=False,out=False)
        msg = "添加成功"

    #添加或修改倒休模块
    compoffmsg = compoff.recordCompoff(emp=emp, date=date, office=False, wh=wh, empop=emp, status=4, approve=0)
    if "成功" not in compoffmsg:
        msg += "," + compoffmsg

    return pubFun.returnMsg(200,message=msg)
