from django.http import HttpResponse,JsonResponse
from django.shortcuts import render
from . import dbfun,emp,leave,pubFun,day as dayPY,constants
from dbModel.models import group_rule,emp_info,attendance_day,day as dayModel
from dbModel.models import ot as otModel, leave as leaveModel
import calendar,datetime

def matchData(request):
    context = {}
    #emps = dbfun.findEmps()

    emps, groupname = dbfun.findGroupEmp()
    #加上老大
    ###boss = dbfun.searchDB(emp_info,emp_id="578624").first()
    biggestGroup = dbfun.searchDB(group_rule,id=1).first()
    biggestEmps = biggestGroup.emp_id.all()
    for biggestEmp in biggestEmps:
        if len(biggestEmp.group_rule_set.all()) == 1:
            emps.append(biggestEmp)
            groupname.append(biggestEmp.group_rule_set.all().values("id", "name"))

    # context["emps"] = emps
    # context["groups"] = groupname
    # print(emps)
    context["emps_groups"] = list(zip(emps,groupname))
    return render(request, 'matchdata.html', context)

def findAttendance(request):
    empID = request.GET.get("empID", None)
    year = request.GET.get("year", 2021)
    month = request.GET.get("month", 5)
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    else:
        emp = None

    if not emp:
        return HttpResponse("未找到员工或员工号错误",status=208)

    #return HttpResponse('<span style="color:red;">test</span>', status=200)

    attendances = dbfun.searchDB(attendance_day,emp_id=emp,date__year=year,date__month=month)

    daysInfo = dbfun.searchDB(dayModel,emp_id=emp,date__year=year,date__month=month)

    ots = dbfun.searchDB(otModel,emp_id=emp,date__year=year,date__month=month,approve__lt=2)

    data = []

    days = calendar.monthrange(int(year), int(month))[1]

    today = datetime.date.today()

    if int(year) == today.year and int(month) == today.month:
        days = today.day - 2

    div = 15#分钟，时间差值，大于此时间会显示为红或绿色

    for d in range(1, days + 1):
        attendance = attendances.filter(date__day=d).first()
        dayInfo = daysInfo.filter(date__day=d).first()
        ot = ots.filter(date__day=d).first()
        date = str(year)+"-"+str(month)+"-"+str(d)

        leaveH = leave.searchLeave(date,emp)[0]

        whDay = dayPY.dateInfo(date)[1]

        hasDayInfoOffice = False
        if dayInfo:
            if dayInfo.st_om or dayInfo.et_o:
                hasDayInfoOffice = True

        if attendance or hasDayInfoOffice or leaveH or ot:
            dict = {}
            dict["date"] = date
            dict["whDay"] = whDay
            officeWH = 0 # 分钟
            systemWH = 0 # 分钟

            if whDay > 0:
                dict["dayType"] = "工作日"
            else:
                dict["dayType"] = "休息日"

            if attendance:
                dict["attfirst"] = pubFun.convertTime(attendance.first,"%H:%M")
                dict["attlast"] = pubFun.convertTime(attendance.last,"%H:%M")
                officeWH = attendance.wh
                dict["attwh"] = attendance.wh#pubFun.convertMinute(attendance.wh)
                if whDay>0:
                    dict["attwhDay"] = officeWH - whDay * 60 - 60
                        #officeWH - constants.STATUTORY_WORKING_HOURS * 60 - 60
                    #whStrColor(officeWH - constants.STATUTORY_WORKING_HOURS * 60 - 60,div)
                else:
                    dict["attwhDay"] = officeWH
            else:
                dict["attfirst"] = "Null"
                dict["attlast"] = "Null"
                dict["attwh"] = "Null"
                if whDay>0:
                    dict["attwhDay"] = -(whDay * 60) #constants.STATUTORY_WORKING_HOURS *60 + 60
                    #'<span style="color:darkred;"> -' + str(constants.STATUTORY_WORKING_HOURS * 60 + 60) + '</span>'
                else:
                    dict["attwhDay"] = 0

            if dayInfo:
                st = str(dayInfo.st_om)
                et = str(dayInfo.et_o)
                color1 = "black"
                color2 = "black"
                if dayInfo.st_om:
                    if attendance:
                        early1, later1, minute1 = pubFun.compareTime(st,str(attendance.first))
                        if minute1 > div:
                            if st == early1:
                                color1 = "red"
                            elif st == later1:
                                color1 = "green"
                    st = '<span style="color:' + color1 + ';">' + pubFun.convertTime(st,"%H:%M") + '</span>'
                else:
                    st = "Null"

                if dayInfo.et_o:
                    if attendance:
                        early2, later2, minute2 = pubFun.compareTime(et, str(attendance.last))
                        if minute2 > div:
                            if et == early2:
                                color2 = "green"
                            elif et == later2:
                                color2 = "red"
                    et = '<span style="color:' + color2 + ';">' + pubFun.convertTime(et, "%H:%M") + '</span>'
                else:
                    et = "Null"

                dict["st"] = st
                dict["et"] = et
                if dayInfo.wh_o:
                    early3, later3, minute3 = pubFun.compareTime(str(dayInfo.st_om),str(dayInfo.et_o))
                    if early3 == str(dayInfo.st_om):
                        systemWH = minute3
                    else:
                        systemWH = 24*60 - minute3
                    dict["wh"] = dayInfo.wh_o#pubFun.convertMinute(dayInfo.wh_o)
                else:
                    dict["wh"] = "Null"
            else:
                dict["st"] = "Null"
                dict["et"] = "Null"
                dict["wh"] = "Null"

            #dict["ot"] = pubFun.convertMinute(ot.ot_hours) if ot else ""
            #dict["leave"] = str(leaveH) + "天" if leaveH else ""
            dict["ot"] = ot.ot_hours if ot else 0
            dict["leave"] = leaveH

            dict["noInfo"] = ""

            if officeWH or systemWH:
                divSR = officeWH - systemWH
            else:
                divSR = 0

            dict["systemWH"] = systemWH
            dict["div"] = divSR#whStrColor(divSR,div)

            data.append(dict)
        else:
            if whDay >0:
                dict = {}
                dict["noInfo"] = "缺勤，未找到当天的任何信息。"
                dict["date"] = date
                data.append(dict)


    #return HttpResponse(data=data,status=201)
    return pubFun.returnMsg(201,data=data)

def whStrColor(divSR,div):
    s = ""

    if divSR > div:
        s = '<span style="color:darkgreen;"> +' + str(divSR) + '</span>'
    elif divSR > 0:
        s = '<span style="color:green;"> +' + str(divSR) + '</span>'
    elif divSR == 0:
        s = divSR
    elif divSR > 0 - div:
        s = '<span style="color:red;"> ' + str(divSR) + '</span>'
    else:
        s = '<span style="color:darkred;"> ' + str(divSR) + '</span>'

    return s

def test(request):
    emp = dbfun.searchDB(emp_info,emp_id="841581").first()
    days = emp.attendance_day_set.all()
    print(days,len(days))
    empID = request.GET.get("empID",None)
    year = request.GET.get("year",2021)
    month = request.GET.get("month",5)
    print(empID,year,month)
    return HttpResponse("done",status=201)

def showReminder(request,reName):
    print("*****************",reName)
    print(render(request, 'reminder/'+reName+'.html', {}));
    return render(request, 'reminder/'+reName+'.html', {});