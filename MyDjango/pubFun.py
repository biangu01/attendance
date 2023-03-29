import time, datetime, json ,os, re
from . import constants
from django.http import HttpResponse,JsonResponse
from PIL import Image
#from deteutil import parser

def compareDate(date1,date2):
    dt_format = "%Y-%m-%d"
    d1 = time.strptime(date1,dt_format)
    d2 = time.strptime(date2, dt_format)
    d = (time.mktime(d1) - time.mktime(d2))/(3600*24)

    if d >= 0:
        d_early = date2
        d_later = date1
    else:
        d_early = date1
        d_later = date2

    return d_early, d_later, abs(d)

def validate_date(date):
    dateformat = "%Y-%m-%d"

    try:
        datetime.datetime.strptime(date,dateformat)
    except:
        return False

    return True

def compareDateTime(datetime1, datetime2):
    """
    输入参数为datetime string格式，如"2021-2-8 9:02"

    输出三个参数分别为
    1、较早的日期 string
    2、较晚的日期 string
    3、时间差，以分钟为单位
    """
    dt_format = "%Y-%m-%d %H:%M"
    t1 = time.strptime(datetime1,dt_format)
    t2 = time.strptime(datetime2,dt_format)
    t = (time.mktime(t1)-time.mktime(t2))/60

    if t >=0 :
        t_early = datetime2
        t_later = datetime1
    else:
        t_early = datetime1
        t_later = datetime2
    
    return t_early,t_later,abs(t)

def compareTime(time1, time2):
    """
    同compareDateTime
    """
    date = "2021-1-1 "
    dt_format = "%Y-%m-%d %H:%M"
    try:
        t1 = time.strptime(date + time1,dt_format)
    except:
        t1 = time.strptime(date + time1,"%Y-%m-%d %H:%M:%S")
    
    try:
        t2 = time.strptime(date + time2,dt_format)
    except:
        t2 = time.strptime(date + time2,"%Y-%m-%d %H:%M:%S")
    
    t = (time.mktime(t1)-time.mktime(t2))/60

    if t >=0 :
        t_early = time2
        t_later = time1
    else:
        t_early = time1
        t_later = time2
    
    return t_early,t_later,abs(t)

 
class DateEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj,datetime.datetime):
            return obj.strftime("%Y-%m-%d %H:%M")
        elif isinstance(obj,datetime.time):
            return obj.strftime("%H:%M")
        elif isinstance(obj,datetime.date):
            return obj.strftime("%Y-%m-%d")
        else:
            return json.JSONEncoder.default(self,obj)
 

def returnMsg(code,message="",**kwargs):
    if code == 201 :#or code == 200:
        if message:
            return HttpResponse(message,status=code)
        else:
            return JsonResponse(kwargs,status=code)
    elif code == 220:
        return JsonResponse(kwargs, status=code)
    else:
        return HttpResponse(message,status=code)

def saveImg(img,empid,name,date,pathType):
    """
    1、把图片转换成最小的格式 pdf 保存pdf格式  --  改成jpg了，可以压缩
    2、将图片保存到固定的路径  日期/员工号_姓名/类型/图片名字
    3、返回图片保存的路径
    参数：
    img：图片 Image类型
    empid： 员工号
    name：姓名
    date： 日期
    pathType： 图片类型，startTime or EndTime or OTRequest
    """
    #111_zhangsan_20210201_startTime.pdf
    imageName = pathType + "_" + empid + "_" + name + "_" + convertDateFormatToPath(date) + ".jpg"
    path = ".\\" + constants.BASE_PATH + "screenshot\\" + convertDateFormatToPath(date,"_") + "\\" + \
           empid + "_" + name + "\\"
    
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)
    pathName = path + imageName

    #Image.open(img).save(pathName)
    i = Image.open(img)

    if i.mode != "RGB":
        i = i.convert("RGB")
    i.save(pathName,quality=50)
    
    return pathName

def convertImg(size,kb):#not use
    """
    等比例压缩长宽，保证二者最大数值为kb
    分辨率会变得较低，本次没有使用
    """
    width = size[0]
    height = size[1]

    a = min(kb/width,kb/height)
    
    return (int(a*width),int(a*height))

def convertDateFormatToPath(date,formate=""):
    """
    参数date的格式为： YYYY-MM-DD
    转换为路径格式：YYYY_MM_DD
    并返回
    """
    return date.replace("-",formate)

def convertNamePinyin(pinyin):
    return pinyin.title().replace(" ","")

def compUpdate(dicOri,dicNew,key,oriVal,newVal):
    if oriVal != newVal:
        dicOri[key] = oriVal
        dicNew[key] = newVal
        return newVal
    else:
        return oriVal

def json_lists(model_list,l_args=None):
    """
    args : 为元祖, 里面的值是dict，数量应和model_list对应
    """
    ls = []
    if l_args and len(l_args) == len(model_list):
        for l,ars in zip(model_list,l_args):
            ls.append(json_dbItem(l,**ars))
    else:
        for l in model_list:
            ls.append(json_dbItem(l))
    return ls

def json_dbItem(item,**kwargs):
    """
    1、字符串前加 u : 后面字符串以 Unicode 格式 进行编码，
    一般用在中文字符串前面，防止因为源码储存格式问题，导致再次使用时出现乱码。
    2、字符串前加 r : 去掉反斜杠的转义机制。  对于变量用repr()
    3、字符串前加 b : 后面字符串是bytes 类型。
    """
    msg = item.viewJson()
    for key, value in kwargs.items():
        msg += ',"'+ str(key) +'":"' + str(value) + '"'
    msg = msg.replace("\\",r"\\")
    msg = re.sub("[\s+]","",msg)
    #print("***",msg,"***")
    return json.loads("{" + msg + "}")

def convertMinute(minute):
    #把分钟变成 小时 +分钟
    symbol = "-" if minute<0 else ""
    div, mod = divmod(abs(minute),60)
    #h = "{}小时 ".format(div) if div else ""
    #m = "{}分钟".format(mod) if mod else ""
    #return h+m
    return "{}{}小时 {}分钟".format(symbol,div,mod)

def convertMinuteToDay(minute):
    #把分钟变成 天 小时 +分钟
    symbol = "-" if minute<0 else ""
    div, mod = divmod(abs(minute),60)
    divDay, modDay = divmod(abs(div),24)
    return "{}{}天 {}小时 {}分钟".format(symbol,int(divDay),int(modDay),int(mod))

def convertHours(hour):
    #把小时变成 天 + 小时
    symbol = "-" if hour<0 else ""
    div, mod = divmod(abs(hour),constants.STATUTORY_WORKING_HOURS)
    return "{}{}天 {}小时".format(symbol,int(div),int(mod))

def convertHoursWithPoint(hour):
    #把小时变成 n.5天
    symbol = "-" if hour<0 else ""
    div, mod = divmod(abs(hour),constants.STATUTORY_WORKING_HOURS/2)
    return "{}{}天".format(symbol,div/2)

def convertTime(t,fm):
    return time.strftime(fm,time.strptime(str(t),"%H:%M:%S"))

def monthDiv(d1,d2):
    """
    返回两个日期的月份差，和是否同年
    """
    if isinstance(d1,str):
        a = d1.split("-")
        ya = int(a[0])
        ma = int(a[1])
    else:
        ya = d1.year
        ma = d1.month

    if isinstance(d2,str):
        b = d2.split("-")
        yb = int(b[0])
        mb = int(b[1])
    else:
        yb = d2.year
        mb = d2.month

    c = (yb - ya) * 12 + mb - ma
    return abs(c), ya==yb

def searchDayLeave(emp,date,approveList):
    from . import day
    wh = day.dateInfo(date,emp=emp)[1]
    if wh == 0:
        return 0
    
    empLeave = emp.leave_set.filter(approve__range=approveList,date__lte=date,date_end__gte=date)
    leaveHours = 0
    for leave in empLeave:
        if monthDiv(date,leave.date)[0]==0:
            if leave.start_duration!=2:
                leaveHours += constants.STATUTORY_WORKING_HOURS
            else:
                leaveHours += constants.STATUTORY_WORKING_HOURS/2
        elif monthDiv(date,leave.date_end)[0]==0:
            if leave.start_duration!=1:
                leaveHours += constants.STATUTORY_WORKING_HOURS
            else:
                leaveHours += constants.STATUTORY_WORKING_HOURS/2
        else:
            leaveHours += constants.STATUTORY_WORKING_HOURS

    return leaveHours

def paraValidate(**kwargs):
    msg = None
    if "empID" in kwargs and not kwargs["empID"]:
        msg = "请求有误，员工号为空"
    if "date" in kwargs and not kwargs["date"]:
        msg = "请求有误，日期为空"
        #returnMsg(208,"请求有误，日期为空")
    return msg
    
def getJsonValue(jsonResult,key,default=None):
    if key in jsonResult:
        return jsonResult[key]
    else:
        return default

def dateFormatForMe(date):
    if not date:
        return ""
    d = str(date)
    arr = d.split(" ")
    if len(arr)>=3:
        arr = arr[:3]
        return "-".join(str(i) for i in arr)
    else:
        arr = arr[0].split("/")
        if len(arr)<3:
            arr = arr[0].split("_")
        if len(arr)<3:
            arr = arr[0].split("-")

        return "-".join(str(i) for i in arr)

def timeFormatForMe(t):
    if not t or str(t) == "nan":
        return None
    arr = str(t).split(":")
    return ":".join(str(i) for i in arr[:2])

def monthDivAccurate(d1,d2=None,divmonth=None,divday=None):
    #判断两个日期是否相差divmonth或divday。如果两个参数都为空，则求相差的月份和日子
    #注：d1应该早于或等于d2
    #多于div时才返回true，小于等于div时返回false
    if not d2:
        d2 = datetime.date.today()

    if isinstance(d1,str):
        a = d1.split("-")
        ya = int(a[0])
        ma = int(a[1])
        ra = int(a[2])
    else:
        ya = d1.year
        ma = d1.month
        ra = d1.day

    if isinstance(d2,str):
        b = d2.split("-")
        yb = int(b[0])
        mb = int(b[1])
        rb = int(b[2])
    else:
        yb = d2.year
        mb = d2.month
        rb = d2.day

    m = abs((yb - ya) * 12 + mb - ma)  # 月份差

    if divmonth:
        if m > divmonth:
            return True
        elif m < divmonth:
            return False
        else:
            if ra < rb:
                return True
            else:
                return False

    r = compareDate(str(ya) + "-" + str(ma) + "-" + str(ra),
                    str(yb) + "-" + str(mb) + "-" + str(rb))[2]
    if divday:
        if r > divday:
            return True
        else:
            return False

    return m,r

def dayBeforeMonth(dt,mon,typ=1):
    """
    返回dt之前mon月的当天
    typ=1返回datetime
    typ=2返回str
    """
    y = dt.year
    m = dt.month
    d = dt.day

    if m-mon <=0:
        y = y-1
        m = 12 + m - mon
    else:
        m = m - mon

    if typ == 1:
        return datetime.datetime(year=y,month=m,day=d)
    elif typ == 2:
        return str(y) + "-" + str(m) + "-" +str(d)