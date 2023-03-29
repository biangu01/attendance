#倒休模块
from django.db.models import Q
from . import dbfun,pubFun,download,day,ot,search,account
from dbModel.models import day as dayModel,ot as otModel,emp_info,compoff
from dbModel.models import compoff_status_choices,compoff_type_overMonth_choices
import datetime
from django.views.decorators.csrf import csrf_exempt

def findCompoff(request):
    #找到所有在职员工
    #emps = dbfun.findEmps().filter(dimission=1)
    today = datetime.date.today()

    begin = datetime.date(2021, 1, 1)
    delta = datetime.timedelta(days=1)
    d = begin

    header = ["员工号","姓名","日期","倒休类型","时长","状态"]
    dayinfo = []
    dayinfoHome = []

    print("查询开始")
    dihs = dbfun.searchDB(dayModel,wh_h__gt=0)

    for dih in dihs:
        #emp = dbfun.searchDB(emp_info,emp_id=dih.emp_id).first()
        dayinfoHome.append([dih.emp_id.emp_id,dih.emp_id.name,dih.date,day.dayType(str(dih.date))+"在家",dih.wh_h,""])

    while d < today:
        typ, wh = day.dateInfo(str(d))
        dis,ots = [],[]

        if typ == 2 or (typ == 4 and wh ==0) or typ == 3:#周末or节假日
            dis = dbfun.searchDB(dayModel,date=d,wh_o__gt=0)
            ots = dbfun.searchDB(otModel,date=d)

            for di in dis:
                ot = ots.filter(emp_id=di.emp_id).first()
                if ot:
                    dayinfo.append(
                        [di.emp_id.emp_id, di.emp_id.name, str(d), "节假日在公司" if typ == 3 else "周末在公司", di.wh_o, "已批" if ot.approve>0 else "未批"])
                else:
                    dayinfo.append(
                        [di.emp_id.emp_id, di.emp_id.name, str(d), "节假日在公司" if typ == 3 else "周末在公司", di.wh_o, "未申请"])

        d += delta
    #return pubFun.returnMsg(201,"Done")
    print("查询完成！准备导出excel")
    return download.downloadCSV("compoff",header,dayinfo,dayinfoHome)

"""
compoff_type_choices = ((1,"周末在公司"),(2,"节假日在公司"),(3,"平日在家"),(4,"周末/节假日在家"))
compoff_approve_choices = ((0,""),(1,"已审批"),(2,"未审批"),(3,"未申请"),(4,"取消"))
compoff_status_choices = ((1,"过期"),(2,"部分使用"),(3,"已使用"),(4,"未使用"),(5,"取消"),(6,"已核销"))
"""
def recordCompoff(compid=None,emp=None,date=None,office=None,
        wh=None,approve=None,empop=None,status=None,whused=None):
    """
    compid:倒休的id，用于leader审批，或取消，或使用状态的修改。有此变量时，emp,date,office,wh为空
    emp:倒休的员工
    date：倒休的日期
    office：是否在公司
    wh：倒休时长 仅添加时用
    approve：倒休的审批状态
    empop：操作人员
    status：倒休的使用状态 (不可和whused同时存在，仅用于改1，5，6)
    whused：本次使用的倒休时长（会自动计算status，所以不需要传status参数，且为2，3，4）
    """
    comptype = None
    if date:
        dayType = day.dayType(date,True)
        #1 - 平日 2 - 周末 3 - 节假日
        if office:
            if dayType == 1:
                return "平日公司无法记录倒休"
            if dayType == 2:
                comptype = 1
            if dayType == 3:
                comptype = 2
        else:
            if dayType == 1:
                comptype = 3
            else:
                comptype = 4
        #如果时间长于3个月以上的，直接status=1
        if status != 1 or status != 6:
            if comptype <=2:
                if pubFun.monthDivAccurate(date,divmonth=3):
                    status = 6
            elif comptype == 4 :
                if pubFun.monthDivAccurate(date,divmonth=3):
                    status = 1
            else:
                if pubFun.monthDivAccurate(date,divmonth=2):
                    status = 1

    if compid:
        comp = dbfun.searchDB(compoff, id=compid).first()
    else:
        comps = dbfun.searchDB(compoff, emp_id=emp, date=date,
               compoff_type=comptype, approve__lt=4)#status__range=[2,4] .first()
        comp = comps.filter(~Q(status=5)).first()

    dicOri = {}
    dicNew = {}
    if comp:
        if comp.status == 5 or comp.approve == 4:
            #已经取消的。不可操作
            return "该倒休的状态为取消，不可修改。"
        if comp.approve == 3:
            return "该倒休的状态为未申请，请先提交ot申请。"
        if comp.status in [1,3,6] :
            #已经过期或使用完的。不可操作
            return "该倒休的状态为"+ dict(compoff_status_choices)[comp.status] +"，不可修改。"
        if empop:
            dicOri["emp"] = ""
            dicNew["emp"] = str(empop.emp_id) + "-" + str(empop.name)
        if comptype and comptype != comp.compoff_type:
            comp.compoff_type = pubFun.compUpdate(dicOri,dicNew,"compoffType",comp.compoff_type,comptype)
        if wh:
            comp.compoff_wh = pubFun.compUpdate(dicOri,dicNew,"compoffWH",comp.compoff_wh,wh)
        if approve:
            comp.approve = pubFun.compUpdate(dicOri,dicNew,"approve",comp.approve,approve)
        if status:
            comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, status)
        if comptype == 2:
            #节假日在公司
            if approve == 1:#已审批
                #取消
                comp.approve = pubFun.compUpdate(dicOri, dicNew, "approve", comp.approve, 4)
                comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, 5)
            elif approve == 4:#取消
                comp.approve = pubFun.compUpdate(dicOri, dicNew, "approve", comp.approve, 0)
                comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, 4)
        if whused:
            t = comp.used_wh + whused
            if t <= comp.compoff_wh and t >= 0:
                comp.used_wh = pubFun.compUpdate(dicOri, dicNew, "status", comp.used_wh, comp.used_wh + whused)
                if t == comp.compoff_wh:
                    comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, 3)
                elif t == 0:
                    comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, 4)
                else:
                    comp.status = pubFun.compUpdate(dicOri, dicNew, "status", comp.status, 2)
            else:
                return "可用时长超限，不可修改。"

        dbfun.updateDB(comp,dicOri,dicNew)
        return "修改成功"
    else:
        if approve == 4 or status == 5:
            #do nothing 用于员工取消ot
            return ""
        #增加新的倒休item
        dbfun.addDB(compoff,emp=emp,emp_id=emp,date=date,compoff_type=comptype,
                    compoff_wh=wh,approve=approve,status=status,used_wh=whused)
        return "添加成功"

def checkCompoff(request):
    empID = request.GET["empID"]
    applyWH = request.GET["wh"]
    emp = dbfun.searchDB(emp_info, emp_id=empID).first()

    leaveRestDict = search.searchAccount(emp)[1]
    msg = ""
    warning = ""
    if leaveRestDict["statAnnualLeave"]>0 :
        warning += "您还有法定年假，本次倒休可能被拒。如需申请，请和您的Leader沟通并确认。"
    if leaveRestDict["compoffNew"] < applyWH:
        msg += "您目前只有{}小时可用的倒休时长，请检查".format(leaveRestDict["compoffNew"]/60)

    if msg:
        return pubFun.returnMsg(208,msg)

    return pubFun.returnMsg(201,msg=msg)

def test(request):
    empID = request.GET["empID"]
    wh = request.GET["wh"]
    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    return pubFun.returnMsg(201,useCompoffAccount(emp,wh))
"""
compoff_type_choices = ((1,"周末在公司"),(2,"节假日在公司"),(3,"平日在家"),(4,"周末/节假日在家"))
compoff_approve_choices = ((0,""),(1,"已审批"),(2,"未审批"),(3,"未申请"),(4,"取消"))
compoff_status_choices = ((1,"过期"),(2,"部分使用"),(3,"已使用"),(4,"未使用"),(5,"取消"),(6,"已核销"))
"""
def useCompoffAccount(emp,wh):
    if wh<=0:
        return []
    #wh按小时算
    compoffs = dbfun.searchDB(compoff,emp_id=emp,approve__lte=1).filter(Q(status=2)|Q(status=4))

    wh = wh * 60#将小时换成分钟
    #倒休顺序： 3 4 1 2
    type_order = [3,4,1,2]

    msg = []
    for i in type_order:
        coms = compoffs.filter(compoff_type=i).order_by("date")
        for com in coms:
            dicOri = {}
            dicNew = {}
            usedwh = com.used_wh if com.used_wh else 0
            #本条可以用时长
            availableWH = account.divTime(com.compoff_wh-usedwh,30)[0]
            if availableWH > 0:
                if wh >= availableWH: # com.compoff_wh - usedwh为本条可用的时长
                    com.used_wh = pubFun.compUpdate(dicOri,dicNew,"usedwh",com.used_wh,com.compoff_wh)
                    com.status = pubFun.compUpdate(dicOri,dicNew,"status",com.status,3)
                    msg.append(str(com.id)+"-"+str(availableWH))
                    wh = wh - availableWH
                else:
                    com.used_wh = pubFun.compUpdate(dicOri,dicNew,"usedwh",com.used_wh,usedwh + wh)
                    com.status = pubFun.compUpdate(dicOri,dicNew,"status",com.status,2)
                    msg.append(str(com.id) + "-" + str(wh))
                    wh = 0
            else:
                com.status = pubFun.compUpdate(dicOri,dicNew,"status",com.status,3)

            dbfun.updateDB(com,dicOri=dicOri,dicNew=dicNew)

            if wh <= 0:
                break

        if wh <= 0:
            break

    return msg

def cancelCompoff(compoffstr):
    # ['121-120', '46-600.0', 'date:2021-7']
    compofflist = compoffstr.replace(" ", "").replace("'", "")[1:-1].split(",")
    compofflist = compofflist[:-1]
    msg = ""

    #做个验证。如果不对，就不能退
    for a in compofflist:
        l = a.split("-")
        if len(l) != 2:
            return "倒休来源不清，无法返还"

    for a in compofflist:
        l = a.split("-")
        id = l[0]
        wh = l[1]
        com = dbfun.searchDB(compoff,id=id).first()
        #这里要判断com的时间，如果超时，那不能返还

        if pubFun.monthDivAccurate(com.date,divmonth=compoff_type_overMonth_choices[com.compoff_type]):
            msg += "{}倒休已过期，无法返还;".format(com.date)
        else:
            dicOri = {}
            dicNew = {}
            usedwh = com.used_wh-wh
            com.used_wh = pubFun.compUpdate(dicOri,dicNew,"compoffUsedWH",com.used_wh,usedwh)
            if usedwh == 0 :
                com.status = pubFun.compUpdate(dicOri,dicNew,"compoffStatus",com.status,4)
            else:
                com.status = pubFun.compUpdate(dicOri, dicNew, "compoffStatus", com.status, 2)
            dbfun.updateDB(com,dicOri=dicOri,dicNew=dicNew)

    msg += "倒休已返还。"
    return msg