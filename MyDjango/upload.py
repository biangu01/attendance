# _*_ coding: utf-8 _*_
from django.views.decorators.csrf import csrf_exempt
from . import pubFun,dbfun,emp,readExcel
import json
import pandas as pd

"""
#not used
@csrf_exempt
def uploadFileJSON(request):
    typ = request.GET['type']

    json_result = json.loads(request.body)

    if typ == "addEmp":
        empList,dupEmp,noValid = emp.addNewPeopleList(json_result)

    if dupEmp or noValid:
        return pubFun.returnMsg(201,msg="添加{}条数据;非法{}条数据;重复{}条数据".format(len(empList),len(noValid),len(dupEmp)),noValid=noValid,dupEmp=dupEmp)
    else:
        return pubFun.returnMsg(201,"成功添加{}条数据".format(len(empList)))
"""

@csrf_exempt
def uploadFile(request):
    typ = request.GET['type']
    file = request.FILES.get("file")

    if typ == "addEmp":
        empList,dupEmp,noValid = readExcel.readExAddEmp(file)
        return emp.addNewPeopleReturnInfo(empList,dupEmp,noValid)
    elif typ == "addInfo":
        readExcel.readExAddInfoJanToMar(file)
        return pubFun.returnMsg(200,"add info done")
    elif typ == "addRecord":
        return pubFun.returnMsg(201,message=readExcel.readAttendance(file))
    elif typ == "addCompoff":
        return pubFun.returnMsg(201,message=readExcel.addCompoff(file))
    else:
        return pubFun.returnMsg(201,msg="无此功能")
