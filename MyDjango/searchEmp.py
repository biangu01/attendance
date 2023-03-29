from dbModel.models import emp_info,ot,leave,day
from . import dbfun,pubFun
import json,datetime
from django.core.paginator import Paginator
from django.db.models import Sum

def search_emp(request):

    empID = request.GET['empID']

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()

    emps,groupname = dbfun.findGroupEmp(emp)

    data = []

    for emp,g in zip(emps,groupname):
        dic = {}
        dic["empID"] = emp.emp_id
        dic["name"] = emp.name
        gIDs = []
        gNames = []
        for i in g:
            gIDs.append(i["id"])
            gNames.append(i["name"])
        dic["groupID"] = gIDs
        dic["groupname"] = gNames
        data.append(dic)

    #return pubFun.returnMsg(201,emps=pubFun.json_lists(emps))#,groups=groups
    return pubFun.returnMsg(201,data=data)

def groupNameRule(groupName):
    """
    整理组名，更清晰一些
    """
    gn = groupName.split("-")
    if gn[0].lower() == "nielsen":
        return "Leader"
    elif len(gn) > 1:
        if gn[1].lower() == "leader":
            return "Leader"
        else:
            return groupName
    else:
        return groupName