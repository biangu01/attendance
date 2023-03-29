# _*_ coding: utf-8 _*_

from . import dbfun,pubFun,search
from dbModel.models import emp_info,account_leave,account_pay,account_compoff,role,group_rule
from dbModel.models import genderDict,dimissionDict
import json,datetime,pypinyin
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def addEmp(request):
    json_result = json.loads(request.body)

    d = {}

    d['empID'] = json_result['empID']
    d['name'] = json_result['name']
    #d['name_pinyin'] = json_result['name_pinyin']
    d['gender'] = genderDict[json_result['gender']]
    d['email'] = json_result['email']
    groupList = json_result['groups']

    d['group'] = ",".join(groupList).lower()
    d['role'] = "emp"

    empop = dbfun.searchDB(emp_info,emp_id=json_result['empopID']).first()
    
    #department = json_result['department']
    #password
    #dimission

    return addNewPeopleReturnInfo(*addNewPeopleList([d],empop))

"""
#not used
def addNewPeople(empid,name,name_pinyin,gender,empop=None):
    if dbfun.searchDB(emp_info,emp_id=empid):
        return "该员工已存在"
    dbfun.addDB(emp_info,emp=empop,emp_id=empid,name=name,name_pinyin=name_pinyin,\
                gender=gender,department="nielseniq",password="123",dimission=1)
    emp = dbfun.searchDB(emp_info,emp_id=empid).first()
    dbfun.addDB(account_leave,emp=empop,emp_id=emp)
    now = datetime.datetime.now()
    dbfun.addDB(account_pay,emp=empop,emp_id=emp,year=now.year,month=now.month)
    dbfun.addDB(account_compoff,emp=empop,emp_id=emp)

    return "添加成功"
"""

def addNewPeopleList(l,empop=None):
    """
    l : list 内容是dict
    """
    empList = []
    accountLeaveList = []
    accountPayList = []
    accountCompoffList = []
    now = datetime.datetime.now()
    dupEmp = []
    noValid = []
    groupDict = {}
    roleDict = {}
    #for i,item in enumerate(l,1):
    for item in l:
        if not ("empID" in item and 'name' in item and 'email' in item and 'group' in item and 'role' in item and 'gender' in item):
            noValid.append(item)
            continue
        if not (item['empID'] and item['name'] and item['email'] and item['group'] and item['role'] and item['gender']):
            noValid.append(item)
            continue
        name_pinyin = pinyin(item['name'])
        emp = emp_info(emp_id=item['empID'],name=item['name'],name_pinyin=name_pinyin,\
                       gender=item['gender'],email=item['email'],\
                       password="123",department="nielseniq",dimission=1)

        alf = dbfun.searchDB(account_leave,emp_id=item['empID'])
        if not alf:
            accountLeaveList.append(account_leave(emp_id=emp))

        for m in range(1,now.month+1):
            apf = dbfun.searchDB(account_pay, emp_id=item['empID'],year=now.year,month=m)
            if not apf:
                accountPayList.append(account_pay(emp_id=emp, year=now.year, month=m))

        acf = dbfun.searchDB(account_compoff, emp_id=item['empID'])
        if not acf:
            accountCompoffList.append(account_compoff(emp_id=emp))

        if dbfun.searchDB(emp_info,emp_id=item['empID']):
            """
            #添加邮箱，成功后注释
            empForTest = dbfun.searchDB(emp_info,emp_id=item['empID']).first()
            if not empForTest.email:
                empForTest.email = item['email']
                dbfun.updateDB(empForTest, dicOri={"email":""}, dicNew={"email":item['email']})
            """
            dupEmp.append(item)
            #continue
            #return "数据库中已存在账户：{}".format(item['empID'])
        else:
            empList.append(emp)
            for g in item['group'].split(","):
                if g in groupDict:
                    groupDict[g].append(emp.emp_id)
                else:
                    groupDict[g] = [emp.emp_id]
            for r in item['role'].split(","):
                if r in roleDict:
                    roleDict[r].append(emp.emp_id)
                else:
                    roleDict[r] = [emp.emp_id]

    if empList:
        dbfun.addDB(emp_info,emp=empop,bulk=True,item_list=empList)
        for key,value in groupDict.items():
            group = dbfun.searchDB(group_rule,name=key).first()
            es = []
            for eid in value:
                es.append(dbfun.searchDB(emp_info,emp_id=eid).first())
            group.emp_id.add(*es)
        for key,value in roleDict.items():
            r = dbfun.searchDB(role,name=key).first()
            es = []
            for eid in value:
                es.append(dbfun.searchDB(emp_info,emp_id=eid).first())
            r.emp_id.add(*es)

    if accountLeaveList:
        dbfun.addDB(account_leave, emp=empop, bulk=True, item_list=accountLeaveList)
    if accountPayList:
        dbfun.addDB(account_pay, emp=empop, bulk=True, item_list=accountPayList)
    if accountCompoffList:
        dbfun.addDB(account_compoff, emp=empop, bulk=True, item_list=accountCompoffList)

    return empList,dupEmp,noValid

def addNewPeopleReturnInfo(empList,dupEmp,noValid):
    if dupEmp or noValid:
        if dupEmp and noValid:
            return pubFun.returnMsg(201,msg="添加{}条数据;非法{}条数据;重复{}条数据".format(len(empList),len(noValid),len(dupEmp)),noValid=noValid,dupEmp=dupEmp)
        elif dupEmp:
            return pubFun.returnMsg(201,msg="添加{}条数据;重复{}条数据".format(len(empList),len(dupEmp)),noValid=noValid,dupEmp=dupEmp)
        elif noValid:
            return pubFun.returnMsg(201,msg="添加{}条数据;非法{}条数据".format(len(empList),len(noValid)),noValid=noValid,dupEmp=dupEmp)
    else:
        return pubFun.returnMsg(201,msg="成功添加{}条数据".format(len(empList)))

def findAllEmps(request):
    page = request.GET.get('pageNo',1)
    itemsInPage = request.GET.get('pageSize', 10)
    empID = request.GET.get('empID',None)

    emp = None
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    
    emps = dbfun.findEmps(emp)
    
    return pubFun.returnMsg(201,total=len(emps),pageSize=int(itemsInPage),data=search.pageForDB(emps,itemsInPage,page)[1])

def getEmpInfo(request):
    empID = request.GET.get('empID',None)

    pubFun.paraValidate(empID=empID)

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    return pubFun.returnMsg(201,data=pubFun.json_dbItem(emp))

# 不带声调的(style=pypinyin.NORMAL)
def pinyin(word):
    s = ''
    n = 1
    for i in pypinyin.pinyin(word, style=pypinyin.NORMAL):
        if n <= 2:
            i = i[0].capitalize()
        s += ''.join(i)
        n += 1
    return s

def findGroup(request):
    empID = request.GET.get('empID',None)

    emp = None
    if empID:
        emp = dbfun.searchDB(emp_info,emp_id=empID).first()
            
    return pubFun.returnMsg(201,data=peopleCountInGroupForEmp(emp))

def peopleCountInGroupForEmp(emp=None):
    #计算emp管理下的每个组有多少人
    #返回字典
    groups = dbfun.findGroupID(emp)
    return peopleCountInGroup(groups)

def peopleCountInGroup(empsgroups):
    d = {}
    for group in empsgroups:
        emps = group.emp_id.all()
        d[group.name] = len(emps)
        
    """
    for qs in empsgroups:
        for group in qs:
            if group["name"] in d:
                d[group["name"]] += 1
            else:
                d[group["name"]] = 1
    """        
    return d

@csrf_exempt
def updateEmp(request):
    json_result = json.loads(request.body)
    empopID = json_result['empopID']#操作人员信息

    emp_info_id = json_result['id']#不可以更改

    emp = dbfun.searchDB(emp_info,id=emp_info_id).first()

    dimission = 1
    if "dimission" in json_result:
        dimission = dimissionDict[json_result['dimission']]

    dicOri = {}
    dicNew = {}
    if dimission == 0:
        if emp.emp_id == empopID:
            return pubFun.returnMsg(208,message="您无法自己修改在职状态，请通知您的Leader")
        else:
            emp.dimission = pubFun.compUpdate(dicOri,dicNew,"dimission",emp.dimission,dimission)
            dbfun.updateDB(emp,dicOri,dicNew,emp=dbfun.searchDB(emp_info,emp_id=empopID).first())
            return pubFun.returnMsg(201,msg="更新成功")
            
    if emp.emp_id == empopID:
        return updateEmpSelf(request)
    
    name = json_result['name']
    name_pinyin = pinyin(name)
    gender = genderDict[json_result['gender']]
    email = json_result['email']

    groupList = [c.lower() for c in json_result['groups']]

    #role = "emp"

    emp.name = pubFun.compUpdate(dicOri,dicNew,"name",emp.name,name)
    emp.name_pinyin = pubFun.compUpdate(dicOri,dicNew,"pinyin",emp.name_pinyin,name_pinyin)
    emp.gender = pubFun.compUpdate(dicOri,dicNew,"gender",emp.gender,gender)
    #emp.dimission = pubFun.compUpdate(dicOri,dicNew,"dimission",emp.dimission,dimission)
    emp.email = pubFun.compUpdate(dicOri,dicNew,"email",emp.email,email)

    #修改组
    groups = dbfun.findGroupIDforEmp(emp)
    groupsNames = [a.name.lower() for a in groups] #现有的组名字
    for group in groups:
        if not group.name in groupList:
            #删除
            group.emp_id.remove(emp)
            pubFun.compUpdate(dicOri,dicNew,"groupDelete",group.name,"")
    for gl in groupList:
        if not gl in groupsNames:
            #增加
            group = dbfun.searchDB(group_rule,name=gl).first()
            group.emp_id.add(emp)
            pubFun.compUpdate(dicOri,dicNew,"groupAdd","",gl)

    dbfun.updateDB(emp,dicOri,dicNew,emp=dbfun.searchDB(emp_info,emp_id=empopID).first())

    return pubFun.returnMsg(201,msg="更新成功")

@csrf_exempt
def updateEmpSelf(request):
    json_result = json.loads(request.body)
    
    empID = json_result['empID']
    name = json_result['name']
    name_pinyin = pinyin(name)
    gender = genderDict[json_result['gender']]
    email = json_result['email']

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    dicOri = {}
    dicNew = {}

    emp.name = pubFun.compUpdate(dicOri,dicNew,"name",emp.name,name)
    emp.name_pinyin = pubFun.compUpdate(dicOri,dicNew,"pinyin",emp.name_pinyin,name_pinyin)
    emp.gender = pubFun.compUpdate(dicOri,dicNew,"gender",emp.gender,gender)
    emp.email = pubFun.compUpdate(dicOri,dicNew,"email",emp.email,email)

    dbfun.updateDB(emp,dicOri,dicNew)

    return pubFun.returnMsg(201,msg="更新成功")

