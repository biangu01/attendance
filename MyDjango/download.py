from django.http import HttpResponse
import csv,datetime,json
from . import dbfun,emp,pubFun,day as dayPY,leave as leavePY,month as monthPY
from dbModel.models import day,emp_info,group_rule,attendance_day
from dbModel.models import leave_type_choices,approve_choices
from dbModel.models import leave as leaveModel, ot as otModel
from django.core.paginator import Paginator
from django.db.models import Sum

def download(request):
    today = datetime.date.today()
    year = request.GET.get('year', today.year)
    month = request.GET.get('month', 0)
    day_ = request.GET.get('day', 0)
    typ = request.GET.get('type', "all")#天，请假，ot，月
    group = request.GET.get('groupID',None)
    empID = request.GET.get('empID',None)
    show = request.GET.get('show',None)
    page = request.GET.get('pageNo', 1)
    itemsInPage = request.GET.get('pageSize', 10)
    emps = []

    if empID:
        emps.append(dbfun.searchDB(emp_info,emp_id=empID).first())
    elif group:
        group_ = dbfun.searchDB(group_rule,id=group)
        emps = dbfun.findGroupEmp(group_=group_)[0]
    else:
        emps = dbfun.findEmps()

    kwarg = {}
    if year:
        kwarg['date__year'] = year
    if month:
        kwarg['date__month'] = month
        #kwarg['date__month__lt'] = 4#month
    if day_:
        kwarg['date__day'] = day_

    context = HttpResponse(content_type='text/csv',status=209)#告诉浏览器是text/csv格式
    context['Content-Disposition'] = 'attachment; filename="somefilename.csv"'# csv文件名，不影响
    context['filename']="somefilename.csv"
    writer = csv.writer(context)

    csvHeader = {"day":['员工号', '姓名', '日期', '上班时间', '下班时间', '当天工作时长', '上班时间-系统',\
                        '上班超时30分钟原因', '在家加班开始时间', '在家加班结束时间', '在家办公时长'],\
                 "leave":['员工号', '姓名', '请假开始日期', '请假结束日期', '请假天数', '请假类型', '原因','审批状态'],\
                 "ot":['员工号', '姓名','日期', '开始时间', '结束时间', '加班时长', '加班类型', '是否为平日', '原因', 'onl号', '饭费', '车费','审批状态'],\
                 "all":['员工号', '姓名', '组', '日期', '上班时间', '下班时间', '当天工作时长(已减午休)', '当天应工作时长','当天结余','上班时间-系统', '上班超时30分钟原因',\
                        '在家加班开始时间', '在家加班结束时间', '在家办公时长', '加班开始时间', '加班结束时间', '加班时长',\
                        '加班类型', '是否为平日', '加班原因', 'onl号', '饭费', '车费','加班审批状态',\
                        '打卡记录上班时间','打卡记录下班时间','打卡记录总时长','系统记录总时长','打卡-系统(分钟)'\
                        ,'对比','打卡时差'],\
                 "month":['员工号', '姓名','月份','打卡记录总时长-小时','本月应上班时长（9小时）-小时',\
                          '系统记录请假时长-天','系统记录申请OT时长-小时','总时长（D+F-E）-小时','是否可批OT']
                 }
    #,'当天请假时长'
    writer.writerow(csvHeader[typ])

    weekday_choices = ((1, "平日"), (2, "周末"), (3, "节假日"), (4, "特殊日期"))
    msg = []

    for emp in emps:
        if typ == "all":
            dayinfo = dbfun.revSearchDB("day",emp,"date",**kwarg)
            otinfo = dbfun.revSearchDB("ot", emp, "date", **kwarg)
            for day in dayinfo:
                items = []
                ots = otinfo.filter(date=day.date)
                d = day.date.strftime("%Y-%m-%d")
                wh = dayPY.dateInfo(d)[1]
                leaveDays = leavePY.searchLeave(d,day.emp_id)[0]
                items += [emp.emp_id,emp.name,emp.empMainGroup(),day.date,day.st_om,day.et_o,pubFun.convertMinute(day.wh_o),\
                          wh,pubFun.convertMinute(day.wh_o-wh*60),day.st_os,day.reason,day.st_h,day.et_h,\
                          pubFun.convertMinute(day.wh_h) if day.wh_h else ""]
                ot_test = ""

                if ots:
                    hasOT = False
                    for ot in ots:
                        if ot.approve < 2:
                            items += [ot.start_time,ot.end_time,float(ot.ot_hours/60),\
                                         dict(ot.ot_type_choices)[ot.ot_type],dict(weekday_choices)[ot.weekday],ot.reason,ot.onl,\
                                         ot.meel_fee,ot.taxi_fee,dict(approve_choices)[ot.approve]]
                            ot_test = ot.end_time
                            hasOT = True
                    if not hasOT:
                        items += [""] * 10
                else:
                    items += [""]*10

                t_early = t_later = t =0
                if day.st_om and day.et_o:
                    t_early, t_later, t = pubFun.compareTime(str(day.st_om), str(day.et_o))
                    if t_early != str(day.st_om):
                        t = 24 * 60 - t

                attendance = emp.attendance_day_set.filter(date=day.date).first()
                if attendance:
                    items.append(attendance.first)
                    items.append(attendance.last)
                    items.append(attendance.wh)
                    items.append(t)
                    items.append(attendance.wh - t)
                    if ot_test:
                        if pubFun.compareTime(str(attendance.last),str(ot_test))[0] == str(attendance):
                            items.append("No")
                        else:
                            items.append("Yes")
                    else:
                        items.append("")
                    items.append(pubFun.compareTime(pubFun.compareTime(str(attendance.first),"09:00")[1],str(attendance.last))[2])
                else:
                    items.append("")
                    items.append("")
                    items.append(0)
                    items.append(t)
                    items.append(0-t)
                    items.append("")
                    items.append("")

                #items += [leaveDays if leaveDays else ""]

                writer.writerow(items)
        elif typ == "month":
            attendance_minutes = dbfun.searchDB(attendance_day,emp_id=emp,date__month=month).aggregate(Sum("wh"))["wh__sum"]
            attendance_minutes = attendance_minutes if attendance_minutes else 0

            #去掉离职的人员
            if not attendance_minutes:
                if emp.dimission == 0:
                    continue

            hours_office_hours = monthPY.whMonthStatutory(int(year),int(month),emp=emp,nineHourOneDay=True)
            leaves = dbfun.searchDB(leaveModel,emp_id=emp,date__month=month,approve__lt=2)
            leave_days = leaves.aggregate(Sum("leave_days"))["leave_days__sum"]
            leave_minutes = 0
            for leave in leaves:
                leave_minutes += leave.leave_days *9*60 if int(leave.leave_days)==leave.leave_days else leave.leave_days *9*60+30
            ot_minutes = dbfun.searchDB(otModel,emp_id=emp,date__month=month,approve__lt=2).aggregate(Sum("ot_hours"))["ot_hours__sum"]
            ot_minutes = ot_minutes if ot_minutes else 0
            totalTime = attendance_minutes + leave_minutes - hours_office_hours*60
            ot_temp = totalTime/60 if ot_minutes > 0 else 0
            if show:
                a = '{"month":"' + str(month) + '月"' + \
                    ',"attendance":' + "%.1f" %(attendance_minutes/60) + \
                    ',"officeHours":' + str(hours_office_hours) + \
                    ',"empID":"' + str(emp.emp_id) + '"' + \
                    ',"name":"' + str(emp.name) + '"' + \
                    ',"totalTime":' + "%.1f" %(ot_temp) + \
                    ',"leaveDays":"' + str(leave_days if leave_days else 0) + '天"' + \
                    ',"ot":' + "%.1f" %(ot_minutes/60) + \
                    ',"otOver":"' + ('ot超时，请检查' if ot_minutes/60 > ot_temp else '') +\
                    '"}'
                # '","otDiv":' + str(totalTime-ot_minutes) +
                msg.append(json.loads(a))
            writer.writerow([emp.emp_id, emp.name, str(month) + "月","%.1f" %(attendance_minutes/60),\
                             hours_office_hours,leave_days,"%.1f" %(ot_temp),\
                             "%.1f" %(totalTime/60), "ot超时，请检查" if ot_minutes/60 > ot_temp else ""])
        else:
            items = dbfun.revSearchDB(typ,emp,"date",**kwarg)
            if typ == "day":
                for day in items:
                    writer.writerow([emp.emp_id,emp.name,day.date,day.st_om,day.et_o,pubFun.convertMinute(day.wh_o),\
                                     day.st_os,day.reason,day.st_h,day.et_h,pubFun.convertMinute(day.wh_h)])
            if typ == "leave":
                for leave in items:
                    if leave.approve <2:
                        writer.writerow([emp.emp_id,emp.name,leave.date,leave.date_end,leave.leave_days,\
                                     dict(leave_type_choices)[leave.leave_type],leave.reason,dict(approve_choices)[leave.approve]])
            if typ == "ot":
                for ot in items:
                    if ot.approve <2:
                        writer.writerow([emp.emp_id,emp.name,ot.date,ot.start_time,ot.end_time,float(ot.ot_hours/60),\
                                     dict(ot.ot_type_choices)[ot.ot_type],dict(weekday_choices)[ot.weekday],ot.reason,ot.onl,\
                                     ot.meel_fee,ot.taxi_fee,dict(approve_choices)[ot.approve]])

    if show:
        total = len(msg)
        msg.sort(key=lambda l: (l["otOver"], int(l["totalTime"])),reverse=True)#多key排序
        msg = list(Paginator(msg, itemsInPage).page(page))
        return pubFun.returnMsg(201, total=total, pageSize=int(itemsInPage), pageNo=int(page), data=msg)
    else:
        return context

def downloadCSV(fileName,header,*args):
    context = HttpResponse(content_type='text/csv', status=209)  # 告诉浏览器是text/csv格式
    context['Content-Disposition'] = 'attachment; filename="'+fileName+'.csv"'  # csv文件名，不影响
    context['filename'] = fileName + ".csv"
    writer = csv.writer(context)

    writer.writerow(header)

    for arg in args:
        for value in arg:
            writer.writerow(value)

    return context
