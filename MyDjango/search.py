from dbModel.models import emp_info,ot,leave,day,group_rule,compoff as compoffDB
from . import dbfun,pubFun,account
from . import leave as leaveModel
from . import month as monthModel
from . import day as dayModel, compoff as compoffModel
import json,datetime
from django.core.paginator import Paginator
from django.db.models import Sum
from django.views.decorators.csrf import csrf_exempt
from django.db.models import Q

def emp_view(request):
    typ = request.GET.get('type',"account")
    empID = request.GET['empID']

    m = pubFun.paraValidate(empID=empID)

    if m:
        return pubFun.returnMsg(208,m)

    year = request.GET.get('year',0)
    month = request.GET.get('month',0)
    day = request.GET.get('day',0)

    today = datetime.date.today()

    if year:
        year = int(year)
    else:
        year = today.year

    if month:
        month = int(month)
    else:
        if typ == "month":
            month = 0
        else:
            month = today.month

    if day:
        day = int(day)
    else:
        day = 0

    page = request.GET.get('pageNo',1)
    itemsInPage = request.GET.get('pageSize', 10)

    #empID = emp_view_get_para_empID(request)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    if not emp:
        return pubFun.returnMsg(208,"员工号为空")

    kwarg = {}
    if year:
        kwarg['date__year']=year
    if month:
        kwarg['date__month']=month
    if day:
        kwarg['date__day']=day

    group = request.GET.get('group',None)
    groupemp = request.GET.get('groupemp',None)
    findemp = group and groupemp

    #找到所有员工的list
    if groupemp:
        emps = [dbfun.searchDB(emp_info,emp_id=groupemp).first()]
    elif group:
        emps = dbfun.findGroupEmp(emp,[dbfun.searchDB(group_rule,id=group).first()])[0]
    else:
        emps = [emp]
    
    items = []
    #根据类别找到对应的QuerySet
    for emp_ in emps:
        if typ == "account":
            sa = searchAccount(emp_)[0]
            #if group or groupemp:
            sa["empID"] = emp_.emp_id
            sa["name"] = emp_.name
            sa["gender"] = emp_.gender
            items.append(sa)
        elif typ == "leave":
            if day:
                a = leaveModel.searchLeaveList(str(year)+"-"+str(month)+"-"+str(day),emp_)
                if a:
                    items.append(a)
            else:
                a = leaveModel.searchLeaveMList(year,month,emp_,returnType=2)
                if a:
                    items = items + a
        elif typ == "compoff":
            a = dbfun.searchDB(compoffDB,emp_id=emp_)
            items = items + pubFun.json_lists(list(a))
        else:
            a = dbfun.revSearchDB(typ,emp_,"-date",**kwarg)
            if a:
                items.append(a)

    total = 0
    if not items:#or not items[0]
        msg = "没有找到相关记录"
    else:
        if typ == "month":
            """
            员工号，姓名，当月应上班时长，当月实际上班时长，当月OT申请时长，当月请假时长，当月总结余
            """
            msg = []
            if year == today.year:
                monthMax = today.month+1
            else:
                monthMax = 13
            for m in range(1,monthMax):
                #当月应上班时长
                whMS = monthModel.whMonthStatutory(year,m,emp=emp)#小时数
                if year==today.year and m == today.month:
                    whMSNow = monthModel.whMonthStatutory(year,m,today.day,emp=emp)#小时数
                    t = emp.day_set.filter(date=today).first()
                    if not t or not t.et_o:
                        whMSNow = whMSNow - 8#减去当天的时长
                else:
                    whMSNow = whMS
                    
                for item,emp in zip(items,emps):
                    its = item.filter(date__year=year,date__month=m)
                    # 当月实际上班时长
                    if its:
                        wh_o = its.aggregate(Sum("wh_o"))["wh_o__sum"]  # 分钟
                    else:
                        wh_o = 0
                    # ot时长
                    ots = dbfun.revSearchDB("ot", emp, date__year=year, date__month=m, approve__lt=2)
                    if ots:
                        ot_hours = ots.aggregate(Sum("ot_hours"))["ot_hours__sum"]  # 分钟
                    else:
                        ot_hours = 0
                    # 请假时长
                    leave_hours = leaveModel.searchLeaveM(year, m, emp)  # 天
                    # 结余时长 = 当月实际上班时长+当月请假时长-当月OT申请时长 - 当月至今应上班时长
                    #print(wh_o,leave_hours,ot_hours,whMSNow,whMS)
                    extraTimeNow = wh_o + leave_hours * 8 * 60 - ot_hours - whMSNow * 60
                    # 结余时长 = 当月实际上班时长+当月请假时长-当月OT申请时长 - 当月应上班时长
                    extraTimeMonth = wh_o + leave_hours * 8 * 60 - ot_hours - whMS * 60

                    a = '{"month":' + str(m) + \
                        ',"whMonStat":"' + str(whMS) + '小时"' +\
                        ',"whO":"' + pubFun.convertMinute(wh_o if wh_o == 0 else wh_o-ot_hours) + '"' + \
                        ',"empID":"' + str(emp.emp_id) + '"' + \
                        ',"name":"' + str(emp.name) + '"' + \
                        ',"whOT":"' + pubFun.convertMinute(ot_hours) + '"' + \
                        ',"whLeave":"' + str(leave_hours) + '天"' + \
                        ',"extraTimeNow":"' + pubFun.convertMinute(extraTimeNow) + '"' + \
                        ',"extraTimeMonth":"' + pubFun.convertMinute(extraTimeMonth) + '"' + \
                        '}'
                    msg.append(json.loads(a))
                    total += 1
            msg = list(Paginator(msg, itemsInPage).page(page))
        elif typ == "account" or typ == "compoff":
            total = len(items)
            msg = list(Paginator(items, itemsInPage).page(page))
        else:
            """
            翻转列表:
            a = [1,2,3] #以下方法都不会改变a的值
            方法一:
            print(reversed(a),type(reversed(a))) 
            #返回迭代器
            #<list_reverseiterator object at 0x00000179CA7606D0> <class 'list_reverseiterator'>
            print(list(reversed(a)),type(list(reversed(a))))
            #[3, 2, 1] <class 'list'>
            方法二:
            print(a[::-1],type(a[::-1]))#[3, 2, 1] <class 'list'>
            方法三:
            print(sorted(a,reverse=True),type(sorted(a,reverse=True)))
            #[3, 2, 1] <class 'list'>
            """
            msg = []
            l_day = []
            for item in items:
                for it in item:
                    if typ == "day" and int(month) > 0:
                        dict_ = {}
                        dict_["cancelOffice"] = 0
                        dict_["cancelHome"] = 0
                        dict_["cancelOffice"],dict_["cancelHome"] = checkRestDay(it,year,month)
                        l_day.append(dict_)
                    msg.append(it)

            total, msg = pageForDB(msg,itemsInPage,page,l_day)
    
    return pubFun.returnMsg(201,total=total,pageSize=int(itemsInPage),pageNo=int(page),data=msg)


def emp_view_Approve(request):
    typ = request.GET.get('type', "leave")
    empID = request.GET['empID']
    approve = request.GET['approve']

    m = pubFun.paraValidate(empID=empID)

    if m:
        return pubFun.returnMsg(208, m)

    page = request.GET.get('pageNo', 1)
    itemsInPage = request.GET.get('pageSize', 10)

    emp = dbfun.searchDB(emp_info, emp_id=empID).first()

    if not emp:
        return pubFun.returnMsg(208, "员工号为空")

    kwarg = {}

    group = request.GET.get('group', None)
    groupemp = request.GET.get('groupemp', None)

    # 找到所有员工的list
    if groupemp:
        emps = [dbfun.searchDB(emp_info, emp_id=groupemp).first()]
    elif group:
        emps = dbfun.findGroupEmp(emp, [dbfun.searchDB(group_rule, id=group).first()])[0]
    else:
        emps = dbfun.findEmps(emp)

    items = []
    # 根据类别找到对应的QuerySet
    for emp_ in emps:
        if typ == "leave":
            a = dbfun.searchDB(leave,emp_id=emp_,approve=approve)
            if a:
                items.append(a)
        elif typ == "ot":
            a = dbfun.searchDB(ot,emp_id=emp_,approve=approve)
            if a:
                items.append(a)

    total = 0
    if not items:  # or not items[0]
        msg = "没有找到相关记录"
    else:
        msg = []
        l_day = []
        for item in items:
            for it in item:
                msg.append(it)
        total, msg = pageForDB(msg, itemsInPage, page, l_day)

    return pubFun.returnMsg(201, total=total, pageSize=int(itemsInPage), pageNo=int(page), data=msg)

@csrf_exempt
def cancelDay(request):
    json_result = json.loads(request.body)
    itemID = json_result['id']
    typ = json_result['type']

    day_ = dbfun.searchDB(day,id=itemID).first()

    off, home = checkRestDay(day_,day_.date.year,day_.date.month)

    if typ == "office" and off:
        dicOri = {}
        dicNew = {}
        day_.st_om = pubFun.compUpdate(dicOri,dicNew,"startTimeManual",day_.st_om,None)
        #day_.st_os = pubFun.compUpdate(dicOri,dicNew,"startTimeSystem",day_.st_os,stsys)
        #day_.reason = pubFun.compUpdate(dicOri,dicNew,"reason",day_.reason,reason)
        day_.et_o = pubFun.compUpdate(dicOri,dicNew,"endTimeOffice",day_.et_o,None)
        #day_.wh = pubFun.compUpdate(dicOri,dicNew,"workHours",day_.wh,workHours)
        day_.wh_o = pubFun.compUpdate(dicOri,dicNew,"workHoursInOffice",day_.wh_o,0)
        account.saveAccountOT(day_.emp_id, day_.date, day_.wh_ot, 0, office=True, apply=False, out=False)
        day_.wh_ot = pubFun.compUpdate(dicOri,dicNew,"workHoursOT",day_.wh_ot,0)
        dbfun.updateDB(day_,dicOri=dicOri,dicNew=dicNew)
    elif typ == "home" and home:
        dicOri = {}
        dicNew = {}
        day_.st_h = pubFun.compUpdate(dicOri,dicNew,"startTimeHome",day_.st_h,None)
        day_.et_h = pubFun.compUpdate(dicOri,dicNew,"endTimeHome",day_.et_h,None)
        account.saveAccountOT(day_.emp_id, day_.date, day_.wh_h, 0, office=False, apply=False,out=False)
        day_.wh_h = pubFun.compUpdate(dicOri,dicNew,"workHoursAtHome",day_.wh_h,0)
        #day_.st_h_path = pubFun.compUpdate(dicOri,dicNew,"startImage",day_.st_h_path,startPath)
        #day_.et_h_path = pubFun.compUpdate(dicOri,dicNew,"endImage",day_.et_h_path,endPath)
        #day_.ot_path = pubFun.compUpdate(dicOri,dicNew,"otImage",day_.ot_path,otPath)
        dbfun.updateDB(day_,dicOri=dicOri,dicNew=dicNew)

    return pubFun.returnMsg(201,msg="更新成功")
    
    
def checkRestDay(dayV,year,month):
    """
    a : cancelOffice ，当天是否有申请的OT
    b : cancelHome ， 当月的在家办公的compoff时长是否够抵扣的
    0 -> 不可以取消
    1 -> 可以
    """
    a = 0
    b = 0
    year = int(year)
    month = int(month)
    today = datetime.date.today()
    #判断相差一个月
    if (today.year == year and today.month - month <=1) or (today.year - year ==1 and today.month ==1 and month == 12):
        it_day = dayV.date
        dateType, workHours = dayModel.dateInfo(str(it_day),emp=dayV.emp_id)
        if workHours == 0:
            if dayV.wh_o > 0 :
                ot_ = dayV.emp_id.ot_emp_id.filter(date=it_day,approve__lt=2).first()
                if not ot_:
                    a = 1
            if dayV.wh_h > 0 :
                h = dayV.wh_h
                compoff = dayV.emp_id.account_compoff_set.filter().first()
                if (today.month == month and compoff.compoff_home1 >= h) or (today.month > month and compoff.compoff_home2 >= h):
                    b = 1
    return a,b

#封装了emp_view()的获取参数部分(只要empID)
def emp_view_get_para_empID(request):
    return request.GET['empID']

#封装了emp_view()的获取参数部分(全都要)
def emp_view_get_para_all(request):
    para_list=[]
    para_list.append(request.GET['type'])
    para_list.append(request.GET['empID'])
    para_list.append(request.GET.get('year',0))
    para_list.append(request.GET.get('month',0))
    para_list.append(request.GET.get('pageNo',1))
    para_list.append(request.GET.get('pageSize', 10))
    return para_list

def emp_view_month(emp,year):
    emp.day_set.filter(date__year=year)

def pageForDB(items,itemsInPage,page,l_args=None):
    # l_args : 要拼接的信息,list，长度要和items相等
    if l_args:
        return len(items),pubFun.json_lists(Paginator(items,itemsInPage).page(page),Paginator(l_args,itemsInPage).page(page))
    else:
        return len(items),pubFun.json_lists(Paginator(items,itemsInPage).page(page))

def searchAccount(emp):
    """
    返回各种年假有几天的dict
    第一个变量是 str 倒休是总和
    第二个变量是 int 倒休是分开的
    """
    a = {}
    b = {}
    items = dbfun.revSearchDB("accountLeave",emp).first()
    a["statAnnualLeave"] = str(float(items.sal)) + "天"
    a["beneAnnualLeave"] = str(float(items.bal)) + "天"
    a["sickLeave"] = str(float(items.sl)) + "天"

    b["statAnnualLeave"] = items.sal
    b["beneAnnualLeave"] = items.bal
    b["sickLeave"] = items.sl

    compoff = 0

    items = dbfun.revSearchDB("accountPay",emp,"year","month",we_ot_lock=0)#小时
    if items:
        l = len(items)
        for item in items:
            compoff += float(item.we_ot)*60
            b["weekEndOT"+str(l)] = float(item.we_ot)*60 #分钟
            l = l-1

    items = dbfun.revSearchDB("accountCompoff",emp).first()#分钟
    compoff += account.divTime(items.compoff_home_wd,30)[0]
    compoff += account.divTime(items.compoff_home_wd2,30)[0]
    compoff += account.divTime(items.compoff_home1,30)[0]
    compoff += account.divTime(items.compoff_home2,30)[0]
    compoff += account.divTime(items.compoff_home3,30)[0]
    compoff += account.divTime(items.compoff_office1,30)[0]
    compoff += account.divTime(items.compoff_office2,30)[0]
    compoff += account.divTime(items.compoff_office3,30)[0]

    b["compoffHomeWD"] = items.compoff_home_wd
    b["compoffHomeWD2"] = items.compoff_home_wd2
    b["compoffHome1"] = items.compoff_home1
    b["compoffHome2"] = items.compoff_home2
    b["compoffHome3"] = items.compoff_home3
    b["compoffOffice1"] = items.compoff_office1 #公司节假日
    b["compoffOffice2"] = items.compoff_office2
    b["compoffOffice3"] = items.compoff_office3

    a["compoff"] = pubFun.convertMinute(compoff)
    b["compoff"] = compoff

    compoff = 0
    comps = dbfun.searchDB(compoffDB,emp_id=emp,approve__lte=1).filter(Q(status=2)|Q(status=4))

    compoff_type_choices = ((1,"weekEndOTNew"),(2,"holidayOTNew"),(3,"wdHomeNew"),(4,"weAndHHomeNew"))
    b["weekEndOTNew"] = 0
    b["holidayOTNew"] = 0
    b["wdHomeNew"] = 0
    b["weAndHHomeNew"] = 0
    for comp in comps:
        usedwh = comp.used_wh if comp.used_wh else 0
        compoff += account.divTime(comp.compoff_wh-usedwh,30)[0]
        b[dict(compoff_type_choices)[comp.compoff_type]] += comp.compoff_wh - usedwh

    a["compoffNew"] = pubFun.convertMinute(compoff)
    b["compoffNew"] = compoff

    return a,b

def test(request):
    print(searchAccount(dbfun.searchDB(emp_info,emp_id=1678224).first()))
    return pubFun.returnMsg(201,"done")
