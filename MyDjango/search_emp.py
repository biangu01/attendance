from dbModel.models import emp_info,ot,leave,day
from . import dbfun,pubFun
import json,datetime
from django.core.paginator import Paginator
from django.db.models import Sum


def search_emp(request):

    empID = request.GET['empID']
    empName=request.GET['name']
    namePinyin=request.GET['name_pinyin']
    department=request.GET['department']
    page = request.GET.get('pageNo',1)
    itemsInPage = request.GET.get('pageSize', 10)

    empList=dbfun.searchDB(emp_info,emp_id=empID)

    return 0