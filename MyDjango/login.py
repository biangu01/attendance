from dbModel.models import emp_info
from . import dbfun,pubFun
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
import json

@csrf_exempt
def login(request):
    json_result = json.loads(request.body)
    
    empID = json_result['empID']#request.POST['empID']
    password = json_result['password']#request.POST['password']

    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    print("login")
    if emp:
        if emp.dimission == 0:
            msg = "该员工已离职"
        elif emp.password == password:
            msg = "登陆成功"
            data = pubFun.json_dbItem(emp)
            roles = emp.role_set.all()
            names = []
            for role in roles:
                functions = role.function_set.all().values("name")
                for fun in functions:
                    if fun not in names:
                        names.append(fun["name"])

            data["rolename"] = names
            return pubFun.returnMsg(201,msg=msg,data=data)
        else:
            msg = "密码错误"
    else:
        msg = "未找到此账户"

    return pubFun.returnMsg(208,msg)
