from . import dbfun,pubFun,constants,search,day
from dbModel.models import emp_info,special_calendar
import json,datetime
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def setHoliday(request):
    json_result = json.loads(request.body)

    holidayID = pubFun.getJsonValue(json_result,"id",None)
    date = pubFun.getJsonValue(json_result,"date","")
    gender = pubFun.getJsonValue(json_result,"gender",0)
    groupList = pubFun.getJsonValue(json_result,"groups",[])
    workhour = pubFun.getJsonValue(json_result,"wh",constants.STATUTORY_WORKING_HOURS)

    date_type = 3 #固定的，特殊日期

    pubFun.paraValidate(date=date)

    if holidayID:
        holiday = dbfun.searchDB(special_calendar,id=holidayID).first()
    else:
        holiday = dbfun.searchDB(special_calendar,date=date).first()
    
    used_for = ""
    if gender or groupList:
        if gender:
            used_for += '"gender":"' + gender + '",'
        if groupList:
            used_for += '"group":"' + ",".join(groupList) + '",'

    if used_for:
        used_for = "{" + used_for[0:-1] + "}"
    
    if holiday:
        #修改
        if holiday.date_type == 1:
            return pubFun.returnMsg(208, message="请不要修改法定节假日")
        dicOri = {}
        dicNew = {}
        holiday.date = pubFun.compUpdate(dicOri,dicNew,"date",holiday.date,date)
        #holiday.work_hours = pubFun.compUpdate(dicOri,dicNew,"workingHours",holiday.work_hours,workhour)
        holiday.used_for = pubFun.compUpdate(dicOri,dicNew,"usedFor",holiday.used_for,used_for if used_for else None)    
        holiday.work_hours_special = pubFun.compUpdate(dicOri,dicNew,"workingHours",holiday.work_hours_special,workhour)
        dbfun.updateDB(holiday, dicOri=dicOri, dicNew=dicNew)
        msg = "更新成功"
    else:
        #新增加的肯定是特殊日期
        dbfun.addDB(special_calendar, date=date, date_type=3,used_for=used_for,work_hours=day.normalDayCheck(date)[1],work_hours_special=workhour)
        msg = "添加成功"

    return pubFun.returnMsg(200, message=msg)

def findSpecialHoliday(request):
    year = request.GET.get("year",datetime.datetime.now().year)
    page = request.GET.get('pageNo', 1)
    itemsInPage = request.GET.get('pageSize', 10)

    holidays = dbfun.searchDB(special_calendar,date__year=year)

    total , data = search.pageForDB(holidays, itemsInPage, page)
    return pubFun.returnMsg(201, total=total, pageSize=int(itemsInPage),data=data)
    
