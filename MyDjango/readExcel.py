import pandas as pd
from . import pubFun,emp,dbfun,dayInOffice,ot
from dbModel.models import groupDict,roleDict,genderDict,account_leave
from django.views.decorators.csrf import csrf_exempt
from dbModel.models import day as modelDay,emp_info,leave as modelLeave,ot as modelOT
from dbModel.models import attendance_day,compoff

def readExAddEmp(file):
    excel = pd.read_excel(file,sheet_name=None)
    """
    参数：
    sheet_name ： 读取哪个sheet 默认0
        None代表全部表
        None和list 返回dict
        int和str   返回DataFrame
    header : 表头，从0开始。默认0

    return: dict {sheetName:DataFrame}
    """
    """
    for key,value in excel.items():
        #key - sheet name
        #value - sheet content  DataFrame
        print(key,value,type(value))
    """
    #upper()大写  lower()小写
    l = []
    for value in excel.values():
        if not value.empty:
            for index,row in value.iterrows():
                #if row['group'].lower() in groupDict:
                row['group'] = row['group'].lower()
                #if row['role'].lower() in roleDict:
                row['role'] = row['role'].lower()
                if row['gender'].lower() in genderDict:
                    row['gender'] = genderDict[row['gender'].lower()]
                l.append(dict(row))
        """
        print(value,type(value),value is None)
        print(value.to_dict,type(value.to_dict))
        print(value.index,type(value.index),value.index is None)
        print(value.columns,type(value.columns))
        a = value.columns.isnull()
        print(a,type(a))
        #print(dir(value.columns))
        """
    return emp.addNewPeopleList(l)

@csrf_exempt
def test(request):
    from dbModel.models import emp_info,role

    emp = dbfun.searchDB(emp_info,emp_id="841581").first()

    dy = modelDay(emp_id=emp,date="2021-04-30",st_om="09:00",reason="no",et_o="18:00")
    dbfun.addDB(modelDay,bulk=True,item_list=[dy])
    return pubFun.returnMsg(200,"good")

def fortestUpdateAccountTo100(request):
    """
    将leave账号改成100，方便传前几个月的信息。一般不使用这个方法
    """
    emps = dbfun.findEmps()
    for emp in emps:
        if emp.emp_id != "578624":
            alf = dbfun.searchDB(account_leave, emp_id=emp).first()
            dicOri = {}
            dicNew = {}
            alf.sl = pubFun.compUpdate(dicOri,dicNew,"sl",alf.sl,100)
            alf.sal = pubFun.compUpdate(dicOri,dicNew,"sal",alf.sal,100)
            alf.bal = pubFun.compUpdate(dicOri,dicNew,"bal",alf.bal,100)
            #以防万一，注释掉更改数据库的脚本，有需要再去掉注释
            #dbfun.updateDB(alf,dicOri=dicOri,dicNew=dicNew)
    return pubFun.returnMsg(200, "To100 Done")

def readExAddInfoJanToMar(file):
    excel = pd.read_excel(file,sheet_name=None,header=0)
    print("start")
    """
    key:sheet name
    row['xxx'] : header name
    """
    for key, value in excel.items():
        if key != "emp":
            if not value.empty:
                value.drop(labels=['name'],axis=1,inplace=True)
                for index, row in value.iterrows():
                    emp = dbfun.searchDB(emp_info, emp_id=str(row["emp_id"]).split(".")[0]).first()
                    if key == "day":
                        dayInOffice.addDayInfo(date=pubFun.dateFormatForMe(row['date']),empID=str(row["emp_id"]).split(".")[0],\
                            stman=pubFun.timeFormatForMe(row['st_om']),et=pubFun.timeFormatForMe(row['et_o']),\
                            reason=row['reason'] if str(row['reason'])!="nan" else "",st_h=pubFun.timeFormatForMe(row['st_h']),\
                            et_h=pubFun.timeFormatForMe(row['et_h']),wh_h=row['wh_h'] if str(row['wh_h'])!="nan" else 0)
                    elif key == "leave":
                        dbfun.addDB(modelLeave, emp_id=emp, date=pubFun.dateFormatForMe(row['date']), \
                                    date_end=row['date_end'], leave_type=row['leave_type'], \
                                    leave_days=row['leave_days'], reason=row['reason'], \
                                    start_duration=row['start_duration'], end_duration=row['end_duration'], \
                                    leave_from=row['leave_from'], approve=row['approve'])
                    elif key == "ot":
                        #empID,otHours,date,startTime,endTime,reason,otType,onl,meelFee,taxiFee,approve
                        ot.addOTInfo(empID=str(row["emp_id"]).split(".")[0],date=pubFun.dateFormatForMe(row['date']), \
                                     startTime=row['start_time'], reason=row['reason'],endTime=row['end_time'],\
                                     otType=row['ot_type'],otHours=row['ot_hours'],approve=row['approve'],\
                                     onl=row['onl'],meelFee=row['meel_fee'] if str(row['meel_fee'])!="nan" else 0,\
                                     taxiFee=row['taxi_fee'] if str(row['taxi_fee'])!="nan" else 0)
                    elif key == "account_leave":
                        """
                        将leave账号更新好。半年用一次，传excel
                        离职的人员不变，  4_26本次更新为初始值。
                        """
                        al = emp.account_leave_set.filter().first()
                        dicOri = {}
                        dicNew = {}
                        al.sl = pubFun.compUpdate(dicOri, dicNew, "sickleave", al.sl, row['sl'] if str(row['sl'])!="nan" else 12)
                        al.sal = pubFun.compUpdate(dicOri, dicNew, "sa_leave", al.sal,
                                                  row['sal'] if str(row['sal']) != "nan" else 2.5)
                        al.bal = pubFun.compUpdate(dicOri, dicNew, "ba_leave", al.bal,
                                                  row['bal'] if str(row['bal']) != "nan" else 40)
                        dbfun.updateDB(al,dicOri=dicOri, dicNew=dicNew)

    print("Done")
    """
    if not value.empty:
        for index, row in value.iterrows():
            # if row['group'].lower() in groupDict:
            row['group'] = row['group'].lower()
            # if row['role'].lower() in roleDict:
            row['role'] = row['role'].lower()
            if row['gender'].lower() in genderDict:
                row['gender'] = genderDict[row['gender'].lower()]
            l.append(dict(row))
    """
"""
def testdata(file):
    excel = pd.read_excel(file, sheet_name=None, header=1)
    for value in excel.values():
        if not value.empty:
            for index,row in value.iterrows():
                emp = dbfun.searchDB(emp_info,emp_id=row['emp_id']).first()
                ot = dbfun.searchDB(modelOT,emp_id=emp,date=row['date']).first()

                if True:
                    ori = ot.start_time
                    ot.start_time = row['start_time']
                    dbfun.updateDB(ot,dicOri={"otStartTime":ori},dicNew={"otStartTime":ot.start_time})
                print(ot)
"""

def readAttendance(file):
    excel = pd.read_excel(file, sheet_name=None)
    notAdd = 0
    update = 0
    itemAddList = []

    for value in excel.values():
        if not value.empty:
            for index,row in value.iterrows():
                empID = str(row["Employee No."]).split(".")[0]
                date = pubFun.dateFormatForMe(row["Date"])
                first = pubFun.timeFormatForMe(row["First In"])
                last = pubFun.timeFormatForMe(row["Last Out"])
                wh = row["Working Hours"]
                if empID:
                    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
                    if emp:
                        attendance = dbfun.searchDB(attendance_day,emp_id=emp,date=date).first()
                        if attendance:
                            if pubFun.timeFormatForMe(attendance.first) == first \
                                    and pubFun.timeFormatForMe(attendance.last) == last :
                                pass
                            else:
                                dicOri = {}
                                dicNew = {}
                                attendance.first = pubFun.compUpdate(dicOri,dicNew,"firstIn",attendance.first,first)
                                attendance.last = pubFun.compUpdate(dicOri,dicNew,"lastOut",attendance.last,last)
                                attendance.wh = pubFun.compUpdate(dicOri,dicNew,"workHours",attendance.wh,wh)
                                dbfun.updateDB(attendance,dicOri=dicOri,dicNew=dicNew)
                                update = update +1
                        else:
                            itemAddList.append(attendance_day(emp_id=emp,date=date,first=first,last=last,wh=wh))
                            #dbfun.addDB(attendance_day,emp_id=emp,date=date,first=first,last=last,wh=wh)
                    else:
                        notAdd += 1
                else:
                    notAdd += 1

    if itemAddList:
        dbfun.addDB(attendance_day,bulk=True,item_list=itemAddList)

    print("{}条添加成功，有{}修改，{}条无法添加".format(len(itemAddList),update,notAdd))

    return "{}条添加成功，有{}修改，{}条无法添加".format(len(itemAddList),update,notAdd)

def addCompoff(file):
    excel = pd.read_excel(file, sheet_name=None)
    itemAddList = []
    for value in excel.values():
        if not value.empty:
            for index,row in value.iterrows():
                empID = str(row["emp_id"])
                date = pubFun.dateFormatForMe(row["date"])
                compoff_type = row["compoff_type"]
                compoff_wh = row["compoff_wh"]
                approve = row["approve"]
                status = row["status"]
                emp = dbfun.searchDB(emp_info,emp_id=empID).first()
                if emp:
                    itemAddList.append(compoff(emp_id=emp,date=date,compoff_type=compoff_type,\
                        compoff_wh=compoff_wh,approve=approve,status=status))

    if itemAddList:
        dbfun.addDB(compoff, bulk=True, item_list=itemAddList)

    print("{}条添加成功".format(len(itemAddList)))
    return "{}条添加成功".format(len(itemAddList))
