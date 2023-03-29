from dbModel.models import special_calendar as sc
from dbModel.models import emp_info,day,group_rule
from django.http import HttpResponse
import json,calendar
from django.views.decorators.csrf import csrf_exempt
from . import dayInOffice,pubFun,constants,log
from django.db.models.query import QuerySet
from django.db.models import Q
from dbModel.models import groupDict,roleDict,genderDict

#将来需要增加记录历史功能

def addHoliday(request):#one time
    #test = sc(DATE='2020-02-11',DATE_TYPE=1,WORK_HOURS=0)
    year = request.GET["year"]
    filename = "D:\\webTool\\MyDjango\\Holiday\\holiday"+year+".json"
    holidays = json.load(open(filename))
    i = 0
    for holiday in holidays:
        h = searchDB(sc,date=holiday['DATE']).first()
        if not h:
            description = holiday['DESCRIPTION'] if 'DESCRIPTION' in holiday else ""
            sc(date=holiday['DATE'],date_type=holiday['DATE_TYPE'],work_hours=holiday['WORK_HOURS'],description=description).save()
            i = i+1
        #这里字段名字的大小写必须要统一
    return HttpResponse("<p>"+"添加成功,"+str(i)+"条</p>")

@csrf_exempt
def findDay(request):
    #date = request.POST['date']
    date = "2021-02-10"

    holiday = findSpecialHoliday(date)

    if holiday:
        pass

    print(holiday)

    return HttpResponse(holiday)


def find(request):
    date = "2021-02-07"
    filename = "D:\\webTool\\MyDjango\\MyDjango\\holiday.json"
    holidays = json.load(open(filename))
    data = {'keyname': 'value'}
    response = HttpResponse()
    response.method = 'POST'
    response.content = '测试'
    response.status_code = 200

    return response
    # item = findWorkHours(date)
    # if not item:
    #     print("BLANK")
    #     return HttpResponse(date)
    # else:
    #     print(item)
    #     return HttpResponse(item[0].id)

def findSpecialHoliday(date):
    return searchDB(sc,date=date)
    #return sc.objects.filter(date=date)#.order_by("id")

#封装基本查找数据库
def searchDB(db,**kwargs):
    """
    __gt : >
    __gte : >=
    __lt : <
    __lte : <=
    __year : 查询年，字段必须是DateField
    __month : 查询月，字段必须是DateField
    __day : 查询日，字段必须是DateField
    __startswith : 以指定字符开头
    __endswith : 以指定字符结尾
    __range : 在 ... 之间，左闭右闭区间，= 号后面为两个元素的列表。如price__range=[200,300]
    __contains ：包含，= 号后面为字符串。
    __icontains ：不区分大小写的包含，= 号后面为字符串。
    """
    return db.objects.filter(**kwargs)

def searchDBByValue(db,*args,**kwargs):
    return db.objects.values(*args).filter(**kwargs)

def revSearchDB(typ, emp, *arg, **kwarg):
    if typ == "ot":
        items = emp.ot_emp_id.filter(**kwarg).order_by(*arg)
    elif typ == "leave":
        items = emp.leave_set.filter(**kwarg).order_by(*arg)
    elif typ == "day":
        items = emp.day_set.filter(**kwarg).order_by(*arg)
    elif typ == "month":
        items = emp.day_set.filter(**kwarg)
    elif typ == "accountLeave":
        items = emp.account_leave_set.filter(**kwarg)
    elif typ == "accountPay":
        items = emp.account_pay_set.filter(**kwarg).order_by(*arg)
    elif typ == "accountCompoff":
        items = emp.account_compoff_set.filter(**kwarg)
        
    return items

def testAdd(request):
    emp = emp_info.objects.filter(emp_id="111").first()
    """
    save介绍
    save()只能增加单条数据，如果需要批量添加，需要先将实例append到列表，然后使用bulk_create添加，也可以for+save()-占用资源
    **********
    save()和create()区别：
    save需要先创建对象，create不用
    *********
    save()和update()区别：
    1. save是将整条记录全部更新一次，没有返回值
    2. update是更新所筛选的数据，返回更新的记录条数
    """
    day(emp_id=emp,date="2021-02-22",wh = 6,st_om="15:18",st_os="17:21",reason="xxxx",et_o="19:21").save()
    #a = day.objects.create(emp_id=emp,date="2021-02-20",wh=8,st_om="15:18",st_os="17:21",reason="xxxx",et_o="19:21")
    return HttpResponse("done")

#封装存数据库方法
def addDB(db,bulk=False,item_list=[],emp=None,task=False,**kwargs):
    if bulk:
        #db.objects.create(item_list)#还没验证
        db.objects.bulk_create(item_list)
    else:
        db(**kwargs).save()
    # 需要添加history的记录
    # 表名：db._meta.db_table
    # emp是操作人员的信息，如果为空，则为task，否则为other 如集体上传等
    if emp:
        try:
            empid, name = emp.emp_id.emp_id, emp.emp_id.name
        except:
            empid, name = emp.emp_id, emp.name
    else:
        empid, name = "0", "task" if task else "other"
    #员工号 : 员工名 : 操作 : 表名 : **[添加的字段名:添加的值]
    message = "{} : {} : add : {} : [{}]".format(empid,name,db._meta.db_table,str(kwargs))
    log.recourdLog(message)

#封装修改数据库的方法
def updateDB(item,dicOri={},dicNew={},emp=None,task=False,**kwargs):
    """
    #还需要记录每个表固定的字段，否则找不到数据
    """
    #return ""
    if kwargs:
        it = item.first()
        item.update(**kwargs)#针对QuerySet类型
        #update后，会将item置为空，可能和is_active参数有关
    else:
        it = item
        item.save()#针对model类型

    # if isinstance(item, QuerySet):
    #     # it = item.first()
    #     print("if isinstance ... ",item)
    #     for i in item:
    #         if i:
    #             it = i
    #             break
    # else:
    #     it = item
    # print("stage1",it)

    if emp:
        empid,name = emp.emp_id,emp.name
    else:
        if task:
            empid, name = "0", "task"
        else:
            if isinstance(item, QuerySet):
                emp = item.first()
            else:
                emp = item
            try:
                empid,name = emp.emp_id,emp.name
            except:
                try:
                    empid,name = emp.emp_id.emp_id,emp.emp_id.name
                except:
                    empid, name = "0", "other"
    # 需要添加history的记录
    # 表名：item._meta.db_table
    # emp是操作人员的信息，如果为空，则为本人操作
    # 员工号 : 员工名 : 操作 : 表名 : **[被修改的字段名:被修改的原值->被修改的值]
    print("stage2",it)
    message = "{} : {} : update : {} : [{}]".format(empid, name, it._meta.db_table, convertdic(dicOri, dicNew))
    log.recourdLog(message)

def convertdic(dicOri,dicNew):
    message = ""

    for key,value in dicOri.items():
        message += str(key) + ":" + str(value) + "->" + str(dicNew[key]) + ", "
    return message

def findGroupID(emp=None,group_=None):#group_ 下一级组
    #找到emp管理下的所有组
    #返回QS，里面是组信息
    leadergroupids = findGroupIDforEmp(emp,group_)

    groupid_ = []
    #用组id 当作父id查找所有组的id
    for groupid in leadergroupids:
        #所有的组id
        gid = searchDB(group_rule,parent_id=groupid.id)
        if gid:
            groupid_ += gid
            g = findGroupID(group_=gid)
            if g:
                groupid_ += g

    return groupid_

def findGroupIDforEmp(emp=None,group_=None):
    #找到emp的所有组
    #返回QS，里面是组信息
    #emp为空时返回最高组的信息
    leadergroupids = []
    if not group_:
        if emp:
            groups = emp.group_rule_set.all()
        else:
            groups = searchDB(group_rule,id=1)
        
        leadergroupids += groups
    else:
        leadergroupids = group_
    return leadergroupids
        
    
def findGroupEmp(emp=None,group_=None,dimission=True): #group_ 当前组
    #找到emp管理下的所有人，及对应的组的名字
    empsgroup = group_ if group_ else findGroupID(emp=emp) 
    emps = []
    empdimission = []
    groupname = [] #gourp information - queryset
    groupnamedimission = []
    if empsgroup:
        #查找所有组id中的员工
        for groupid in empsgroup:
            emps_ = groupid.emp_id.all()
            for emp in emps_:
                if emp.dimission == 0:
                    if emp not in empdimission:
                        empdimission.append(emp)
                        groupnamedimission.append(emp.group_rule_set.all().values("id","name"))
                else:
                    if emp not in emps:
                        emps.append(emp)
                        groupname.append(emp.group_rule_set.all().values("id","name"))

    if dimission:
        return emps + empdimission, groupname + groupnamedimission
    else:
        return emps, groupname

def findEmps(emp=None,**kwargs):
    #找到emp管理下的所有人,包含emp
    #如果emp为空，找到所有人
    if emp:
        emps = findGroupEmp(emp)[0]
        if emp not in emps:
            emps.append(emp)
        return emps
    else:
        return searchDB(emp_info,**kwargs).all()

#@csrf_exempt
def test(request):
    empID = request.GET['empid']
    from dbModel.models import emp_info
    emp = searchDB(emp_info,emp_id=empID).first()
    
    return HttpResponse(findGroupEmp(emp=emp))
    














    
