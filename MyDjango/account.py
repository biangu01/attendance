from . import dbfun,pubFun,day,search,constants
from dbModel.models import emp_info,account_leave,account_pay,account_compoff,leave_type_choices_dbName
from dbModel.models import day as db_day
from django.http import HttpResponse
from django.db.models.query import QuerySet
import datetime

#key都没有用
def useLeaveAccount(emp,wh=0,leaveType=0,leaveRestDict={},compoff=[]):
    #申请和取消假期的操作
    #wh 以天为单位

    compoffDict = {"compoffHome1":1,"compoffHome2":2,"compoffHome3":3,\
                    "compoffOffice1":7,"compoffOffice2":8,"compoffOffice3":9,\
                    "weekEndOT1":4,"weekEndOT2":5,"weekEndOT3":6,\
                   "compoffHomeWD":11,"compoffHomeWD2":12}

    if compoff:
        #有compoff证明有来自哪里，是要取消操作
        #[20-2,3-2, 2-2, 1, 9, 8, 7, '6-4-2021-1', '5-2021-2', '4-2021-3', date:2021-02]
        compoff = compoff.replace(" ","").replace("'","")[1:-1].split(",")
        d = compoff[-1].split(":")
        compoff = compoff[:-1]
        now = datetime.datetime.now()

        div,sameYear = pubFun.monthDiv(d[1],now)
        #mt2M = div > 1
        #mt3M = div > 2

        msg = ""
        #we3l = 1
        #itemTemp = None
        #year_ = 0
        #month_ = 0

        for a in compoff:
            l = a.split("-")
            if True:
            #for comp in l:
                typ = int(l[0])
                wh = float(l[1])
                #这里wh已经取好单位了。不是 天 了。
                if len(l) > 2:
                    year = l[2]
                    month = l[3]

                if typ == 10:
                    item = emp.account_leave_set.filter().first()
                    app = item.sal
                    item.sal = item.sal + wh
                    if sameYear:
                        dbfun.updateDB(item,{"StatutoryAnnualLeave":app},{"StatutoryAnnualLeave":item.sal})
                    else:
                        msg += "法定年假{}天，无法返还".format(abs(wh))
                elif typ == 20:
                    item = emp.account_leave_set.filter().first()
                    app = item.bal
                    if item.bal + wh > constants.BAL_LEAVE_UP_LIMIT:
                        item.bal = constants.BAL_LEAVE_UP_LIMIT
                        msg += "福利年假{}天，多于上限，无法返还".format(app + wh - constants.BAL_LEAVE_UP_LIMIT)
                    else:
                        item.bal = item.bal + wh
                    dbfun.updateDB(item,{"BenefitAnnualLeave":app},{"BenefitAnnualLeave":item.bal})
                elif typ == 30:
                    item = emp.account_leave_set.filter().first()
                    app = item.sl
                    item.sl = item.sl + wh
                    if sameYear:
                        dbfun.updateDB(item,{"SickLeave":app},{"SickLeave":item.sl})
                    else:
                        msg += "病假{}天，无法返还".format(abs(wh))
                elif typ == 80:
                    item = emp.account_leave_set.filter().first()
                    app = item.lwp
                    item.lwp = item.lwp + wh
                    dbfun.updateDB(item,{"LeaveWithoutPay":app},{"LeaveWithoutPay":item.lwp})
                elif div > 2:
                    msg += "倒休假期{}天，已经超限，无法返还".format(abs(wh))
                elif typ == 1:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2 :
                        app = item.compoff_home3
                        temp = item.compoff_home3 = item.compoff_home3 + wh
                        dbfun.updateDB(item, {"compoffHome3": app}, {"compoffHome3": temp})
                    elif div == 1:
                        app = item.compoff_home2
                        temp = item.compoff_home2 = item.compoff_home2 + wh
                        dbfun.updateDB(item, {"compoffHome2": app}, {"compoffHome2": temp})
                    else:
                        app = item.compoff_home1
                        temp = item.compoff_home1 = item.compoff_home1 + wh
                        dbfun.updateDB(item, {"compoffHome1": app}, {"compoffHome1": temp})
                elif typ == 2:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2:
                        msg += "周末在家倒休{}天，无法返还\t".format(abs(wh))
                    elif div == 1:
                        app = item.compoff_home3
                        temp = item.compoff_home3 = item.compoff_home3 + wh
                        dbfun.updateDB(item, {"compoffHome3": app}, {"compoffHome3": temp})
                    else:
                        app = item.compoff_home2
                        temp = item.compoff_home2 = item.compoff_home2 + wh
                        dbfun.updateDB(item,{"compoffHome2":app},{"compoffHome2":temp})
                elif typ == 3:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2 or div == 1:
                        msg += "周末在家倒休{}天，无法返还\t".format(abs(wh))
                    else:
                        app = item.compoff_home3
                        temp = item.compoff_home3 = item.compoff_home3 + wh
                        dbfun.updateDB(item,{"compoffHome3":app},{"compoffHome3":temp})
                elif typ == 7:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2 :
                        app = item.compoff_office3
                        temp = item.compoff_office3 = item.compoff_office3 + wh
                        dbfun.updateDB(item, {"compoffOffice3": app}, {"compoffOffice3": temp})
                    elif div == 1:
                        app = item.compoff_office2
                        temp = item.compoff_office2 = item.compoff_office2 + wh
                        dbfun.updateDB(item, {"compoffOffice2": app}, {"compoffOffice2": temp})
                    else:
                        app = item.compoff_office1
                        temp = item.compoff_office1 = item.compoff_office1 + wh
                        dbfun.updateDB(item,{"compoffOffice1":app},{"compoffOffice1":temp})
                elif typ == 8:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2:
                        msg += "节假日在公司倒休{}天，无法返还\t".format(abs(wh))
                    elif div == 1:
                        app = item.compoff_office3
                        temp = item.compoff_office3 = item.compoff_office3 + wh
                        dbfun.updateDB(item, {"compoffOffice1": app}, {"compoffOffice1": temp})
                    else:
                        app = item.compoff_office2
                        temp = item.compoff_office2 = item.compoff_office2 + wh
                        dbfun.updateDB(item,{"compoffOffice2":app},{"compoffOffice2":temp})
                elif typ == 9:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2 or div == 1:
                        msg += "节假日在公司倒休{}天，无法返还\t".format(abs(wh))
                    else:
                        app = item.compoff_office3
                        item.compoff_office3 = item.compoff_office3 + wh
                        dbfun.updateDB(item,{"compoffOffice3":app},{"compoffOffice3":item.compoff_office3})
                elif typ == 11:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2:
                        msg += "平日在家倒休{}天，无法返还\t".format(abs(wh))
                    if div == 1:
                        app = item.compoff_home_wd2
                        item.compoff_home_wd2 = item.compoff_home_wd2 + wh
                        dbfun.updateDB(item, {"compoffHomeWD2": app}, {"compoffHomeWD2": item.compoff_home_wd2})
                    else:
                        app = item.compoff_home_wd
                        item.compoff_home_wd = item.compoff_home_wd + wh
                        dbfun.updateDB(item, {"compoffHomeWD": app}, {"compoffHomeWD": item.compoff_home_wd})
                elif typ == 12:
                    item = emp.account_compoff_set.filter().first()
                    if div == 2 or div == 1:
                        msg += "平日在家倒休{}天，无法返还\t".format(abs(wh))
                    else:
                        app = item.compoff_home_wd2
                        item.compoff_home_wd2 = item.compoff_home_wd2 + wh
                        dbfun.updateDB(item, {"compoffHomeWD2": app}, {"compoffHomeWD2": item.compoff_home_wd2})
                else:#elif typ == 4 or 5 or 6:
                    item = emp.account_pay_set.filter(year=year,month=month).first()
                    if item.we_ot_lock > 0 :
                        msg += "周末在公司倒休{}天，无法返还\t".format(abs(wh))
                    else:
                        app = item.we_ot
                        item.we_ot = item.we_ot + wh
                        dbfun.updateDB(item, {"compoffWE" + str(year) + str(month): app},
                                       {"compoffWE" + str(year) + str(month): item.we_ot})
                    """
                    if mt3M:
                        if we3l == 1:
                            msg += "周末在公司倒休{}天，无法返还\t".format(abs(wh))
                            itemTemp = item
                            year_ = year
                            month_ = month
                        else:
                            app = itemTemp.we_ot
                            itemTemp.we_ot = itemTemp.we_ot + wh
                            dbfun.updateDB(item, {"compoffWE" + str(year_) + str(month_): app},
                                           {"compoffWE" + str(year_) + str(month_): itemTemp.we_ot})
                            itemTemp = item
                            year_ = year
                            month_ = month
                        we3l += 1
                    else:
                        app = item.we_ot
                        item.we_ot = item.we_ot + wh
                        dbfun.updateDB(item,{"compoffWE"+str(year)+str(month):app},{"compoffWE"+str(year)+str(month):item.we_ot})
                    """

        return msg

    #下面是申请
    if leaveType == 1:
        item = emp.account_leave_set.filter().first()
        app = item.sal
        item.sal = item.sal + wh
        compoff = [str(10)+"-"+str(abs(wh))]
        dbfun.updateDB(item,{"StatutoryAnnualLeave":app},{"StatutoryAnnualLeave":item.sal})
    elif leaveType == 2:
        item = emp.account_leave_set.filter().first()
        app = item.bal
        item.bal = item.bal + wh
        compoff = [str(20)+"-"+str(abs(wh))]
        dbfun.updateDB(item,{"BenefitAnnualLeave":app},{"BenefitAnnualLeave":item.bal})
    elif leaveType == 3:
        item = emp.account_leave_set.filter().first()
        app = item.sl
        item.sl = item.sl + wh
        compoff = [str(30)+"-"+str(abs(wh))]
        dbfun.updateDB(item,{"SickLeave":app},{"SickLeave":item.sl})
    elif leaveType == 8:
        item = emp.account_leave_set.filter().first()
        app = item.lwp 
        item.lwp = item.lwp + wh
        compoff = [str(80)+"-"+str(abs(wh))]
        dbfun.updateDB(item,{"LeaveWithoutPay":app},{"LeaveWithoutPay":item.lwp})
    elif leaveType == 4:
        if not leaveRestDict:
            leaveRestDict = search.searchAccount(emp)[1]

        compoff = []
        #时间 天 -》 分钟
        wh = wh * constants.STATUTORY_WORKING_HOURS * 60

        if wh != 0:
            key = "compoffHomeWD2"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_home_wd2
                if app >= abs(wh):
                    item.compoff_home_wd2 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_home_wd2 = divTime(app, 30)
                    wh = wh + wh_
                    #item.compoff_home_wd2 = 0
                    #wh = app + wh
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_home_wd2))
                dbfun.updateDB(item,{key:app},{key:item.compoff_home_wd2})
        if wh != 0:
            key = "compoffHomeWD"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_home_wd
                if app >= abs(wh):
                    item.compoff_home_wd = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_home_wd = divTime(app, 30)
                    wh = wh + wh_
                    #item.compoff_home_wd = 0
                    #wh = app + wh
                #compoff记录这个假期 使用的是  哪个类型 - 用了多长时间 - 来自哪年哪月（如果有此字段）
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_home_wd))
                dbfun.updateDB(item,{key:app},{key:item.compoff_home_wd})
        if wh != 0:
            key = "compoffHome3"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_home3
                if app >= abs(wh):
                    item.compoff_home3 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_home3 = divTime(app, 30)
                    wh = wh + wh_
                    #item.compoff_home3 = 0
                    #wh = app + wh
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_home3))
                dbfun.updateDB(item,{key:app},{key:item.compoff_home3})
        if wh != 0:
            key = "compoffHome2"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_home2
                if app >= abs(wh):
                    item.compoff_home2 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_home2 = divTime(app, 30)
                    wh = wh + wh_
                    #item.compoff_home2 = 0
                    #wh = app + wh
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_home2))
                dbfun.updateDB(item,{key:app},{key:item.compoff_home2})
        if wh != 0:
            key = "compoffHome1"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_home1
                if app >= abs(wh):
                    item.compoff_home1 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_home1 = divTime(app, 30)
                    wh = wh + wh_
                    #wh = app + wh
                    #item.compoff_home1 = 0
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_home1))
                dbfun.updateDB(item,{key:app},{key:item.compoff_home1})
        if wh != 0:
            key = "compoffOffice3"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_office3
                if app >= abs(wh):
                    item.compoff_office3 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_office3 = divTime(app, 30)
                    wh = wh + wh_
                    #wh = app + wh
                    #item.compoff_office3 = 0
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_office3))
                dbfun.updateDB(item,{key:app},{key:item.compoff_office3})
        if wh != 0:
            key = "compoffOffice2"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_office2
                if app >= abs(wh):
                    item.compoff_office2 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_office2 = divTime(app, 30)
                    wh = wh + wh_
                    #wh = app + wh
                    #item.compoff_office2 = 0
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_office2))
                dbfun.updateDB(item,{key:app},{key:item.compoff_office2})
        if wh != 0:
            key = "compoffOffice1"
            if leaveRestDict[key] > 0:
                item = emp.account_compoff_set.filter().first()
                app = item.compoff_office1
                if app >= abs(wh):
                    item.compoff_office1 = app + wh
                    wh = 0
                else:
                    wh_, item.compoff_office1 = divTime(app, 30)
                    wh = wh + wh_
                    #wh = app + wh
                    #item.compoff_office1 = 0
                compoff.append(str(compoffDict[key])+"-"+str(app-item.compoff_office1))
                dbfun.updateDB(item,{key:app},{key:item.compoff_office1})
        if wh != 0:
            wh = float(wh/60)
            items = emp.account_pay_set.filter(we_ot_lock=0).order_by("year","month")
            l = len(items)
            for item in items:
                app = item.we_ot
                if app > 0:
                    key = "weekEndOT" + str(l)
                    if app >= abs(wh):
                        item.we_ot = app + wh
                        wh = 0
                    else:
                        wh = app + wh
                        item.we_ot = 0
                    compoff.append(str(compoffDict[key])+"-"+str(app-item.we_ot)+"-"+str(item.year)+"-"+str(item.month))
                    dbfun.updateDB(item,{key:app},{key:item.we_ot})
                l = l-1
            
    return compoff

def saveAccountOT(emp,date,whOld,whNew,office=True,apply=False,out=False):
    #out 是否从账户中提出 没有用了
    #单位 小时
    """
    当apply为True时，需要考虑日期跨月
    如果是存，out =False ： compoff的月清的账户直接舍弃，三月清和pay的存入上个月
    如果是取，out = True  只有ot被取消：compoff的月清的账户不做处理，三月清和pay的从上个月取，如果为0，记为负数
    在下面的方法改，即可
    """
    wh = whNew - whOld #分钟
    if wh != 0:
        #找到 哪个数据库 哪个字段
        itemQuerySet,name,value,key,unit = accountItemOT(emp,str(date),office=office,apply=apply,out=out)

        if not itemQuerySet:
            if wh > 0:
                return "OT已过期，无法保存\n"
            else:
                return "OT已过期，无法返还到倒休账户\n"

        if unit == "hr":
            wh = wh/60

        #用QuerySet类型，因为.update方法
        if isinstance(value,int) or isinstance(value,float):
            wh_ = value + wh
        else:
            wh_ = sum(value) + wh

        if itemQuerySet:
            if wh_ < 0 and name != "compoff_office_wd":
                return "Error hours < 0"
            else:
                if isinstance(value,int) or isinstance(value,float):
                    dbfun.updateDB(itemQuerySet,{name:value},{name:wh_},**{name:wh_})
                    return str(wh) + "时长已经存入\n"#更新时长
                else:
                    #从3个月内的，排序修改
                    count = 0
                    whTemp = wh
                    for v in value:
                        if v + whTemp < 0:
                            if isinstance(name,str):
                                dbfun.updateDB(itemQuerySet[count],{name:v},{name:0},**{name:0})
                            else:
                                dbfun.updateDB(itemQuerySet,{name[count]:v},{name[count]:0},**{name[count]: 0})
                            whTemp = v + whTemp
                        else:
                            if isinstance(name, str):
                                dbfun.updateDB(itemQuerySet[count],{name:v},{name:v+whTemp},**{name: v+whTemp})
                            else:
                                dbfun.updateDB(itemQuerySet,{name[count]:v},{name[count]:v+whTemp},**{name[count]: v+whTemp})
                            whTemp = v + whTemp
                            if whTemp == 0:
                                break
                    return str(wh) + "时长已经存入\n"
                    #return "account updated"
        else:
            return "Not Find account\n"
    else:#时间没有变
        return "No Update\n"#什么都不做

def accountItemOT(emp,date,office=True,apply=False,out=False):
    """
    枚举法
    返回 1 queryset类型的item  2 修改的字段名  3 修改的原始值  4 history用的key 5 时间单位
    """
    """
    1 - 平日
    2 - 周末
    3 - 节假日
    """
    dateType = day.dateInfo(date)[0]
    if dateType == 4:
        dateType = 1

    d = date.split("-")
    year = d[0]
    month = d[1]

    div = pubFun.monthDiv(date,datetime.datetime.now())[0]
    sameMonth = (div == 0)

    unit = "min"

    if not office:
        if dateType == 1: #这个要改成2个月
            #平日在家，只有员工
            if sameMonth:
                item = emp.account_compoff_set.filter()
                name = "compoff_home_wd"
                value = item.first().compoff_home_wd
                key = "workDayCompoffHome"
            elif div == 1 :
                item = emp.account_compoff_set.filter()
                name = "compoff_home_wd2"
                value = item.first().compoff_home_wd2
                key = "workDayCompoffHome"
            else:
                item = None
                name = ""
                value = None
                key = ""
        else:
            #周末节假日在家
            item = emp.account_compoff_set.filter()
            if sameMonth:
                """
                if out:
                    # 这个没什么用，写在倒休的模块中了
                    name = ["compoff_home3","compoff_home2","compoff_home1"]
                    value = [item.first().compoff_home3,item.first().compoff_home2,item.first().compoff_home1]
                else:
                """
                name = "compoff_home1"
                value = item.first().compoff_home1
            elif div == 1:
                name = "compoff_home2"
                value = item.first().compoff_home2
            elif div == 2:
                name = "compoff_home3"
                value = item.first().compoff_home3
            else:
                item = None
                name = ""
                value = None
                key = ""
            key = "weekEndOrHolidayCompoffHome"
    else:#在公司
        if dateType == 1:
            #平日在公司
            if apply:
                # 不用out变量，因为是否取消ot，都是同样的字段和处理方法
                # 不用sameMonth，因为都是按照当前item的时间存取
                item = emp.account_pay_set.filter(year=year,month=month)
                name = "wd_ot"
                value = item.first().wd_ot#*60
                key = "workDayOfficePay"
                unit = "hr"
            else:
                if sameMonth:
                    item = emp.account_compoff_set.filter()
                    name = "compoff_office_wd"
                    value = item.first().compoff_office_wd
                    key = "workDayOfficeCompoff"
                else:
                    item,name,value,key = None,"",None,""
        elif dateType == 2:
            if apply:
                item = emp.account_pay_set.filter(year=year,month=month,we_ot_lock=0)#.order_by("year","month")
                name = "we_ot"
                value = item.first().we_ot#*60
                key = "weekEndOfficePay"
                unit = "hr"
            else:
                if sameMonth:
                    item = emp.account_compoff_set.filter()
                    name = "compoff_office_we"
                    value = item.first().compoff_office_we
                    key = "weekEndOfficeCompoff"
                else:
                    item,name,value,key = None,"",None,""
        elif dateType == 3:
            if apply:
                #不用out变量，因为是否取消ot，都是同样的字段和处理方法
                item = emp.account_pay_set.filter(year=year,month=month)
                name = "holiday_ot"
                value = item.first().holiday_ot#*60
                key = "HolidayOfficePay"
                unit = "hr"
            else:
                item = emp.account_compoff_set.filter()
                if sameMonth:
                    """
                    if out:
                        #这个没什么用，写在倒休的模块中了
                        name = ["compoff_office3","compoff_office2","compoff_office1"]
                        value = [item.first().compoff_office3,item.first().compoff_office2,item.first().compoff_office1]
                    else:
                    """
                    name = "compoff_office1"
                    value = item.first().compoff_office1
                elif div == 1:
                    name = "compoff_office2"
                    value = item.first().compoff_office2
                elif div == 2:
                    name = "compoff_office3"
                    value = item.first().compoff_office3
                else:
                    item, name, value, key = None, "", None, ""
                key = "HolidayOfficeCompoff"
        else:
            #没有其他类型了
            pass
    return item,name,value,key,unit

def divTime(t,base):
    """
    根据base的时间段，判断可削减的最大时间长度
    返回 可扣除的时间 , 剩余的时间
    """
    if t <= 0:
        return 0,t
    n = 1
    while t >= base*n:
        n += 1
    t1 = base*(n-1)
    return t1,t-t1