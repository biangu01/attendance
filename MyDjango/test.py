from dbModel.models import emp_info,day,account_pay,account_leave,account_compoff
from . import search,dbfun,pubFun,task

def test(request):
    task.updateCompoffTask()
    return pubFun.returnMsg(200,"done")