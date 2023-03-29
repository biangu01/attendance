# -*-coding:utf-8 -*-
from django.db import models
from MyDjango import pubFun
import json

# Create your models here.

approve_choices=((0,"待审批"),(1,"已审批"),(2,"取消"))
leave_type_choices=((1,"法定年假"),(2,"福利年假"),(3,"病假"),(4,"倒休"),(5,"Compassionate leave"),(6,"计划生育假"),(7,"陪产假"),(8,"无薪假"),(9,"产检假"))
#Compassionate leave 恩假
leave_type_choices_dbName=((1,"sal"),(2,"bal"),(3,"sl"),(4,"compoff"),(5,"cl"),(6,"fpl"),(7,"pl"),(8,"lwp"))

genderDict = {"男":1,"女":2,1:1,2:2,"1":1,"2":2}
groupDict = {"nielsen":1,"setup-leader":2,"coding":3,"table":4,"setup-confirmit_ci":5,"setup-confirmit_ip":6,
             "setup-decipher":7,"setup-surveytogo":8,"setup-other":9,"setup-dd":10,"coding-leader":11,
             "table-leader":12,"other":13}
groupAbbreviationDict = {1:"nielsen",2:"setup",3:"coding",4:"table",5:"setup",6:"setup",
             7:"setup",8:"setup",9:"setup",10:"dd",11:"coding",
             12:"table",13:"other"}
roleDict = {"projectleader":1,"teamleader":2,"subteamleader":3,"emp":4,"other":5,"adminstrator":6}

otTypeDict = {"setup":{1:"A1：新增需要、修改多",2:"A2：临时增加项目、需求或者修改",3:"A3：资料提供晚，拖延",
                       4:"B1：效率低",5:"B2：正确率低",6:"C：协助其他组员，或者SPC项目"},
              "coding":{21:"数据量大/时间紧张",22:"特殊要求",23:"协助其他组员"},
              "table":{41:"等数据",42:"需求晚",43:"需求多",44:"QC",45:"项目时间紧",46:"车展",47:"应CS要求standby",
                       48:"待交付项目多",49:"协助其他组员",50:"加班等跑表完成后当天交付"},
              "other":{61:"工作繁重"}}
dimissionDict = {"离职":0,"在职":1}

compoff_type_choices = ((1,"周末在公司"),(2,"节假日在公司"),(3,"平日在家"),(4,"周末/节假日在家"))
compoff_type_overMonth_choices = {1:3,2:3,3:2,4:3}#过期的月份，对应type
compoff_approve_choices = ((0,""),(1,"已审批"),(2,"未审批"),(3,"未申请"),(4,"取消"))
compoff_status_choices = ((1,"过期"),(2,"部分使用"),(3,"已使用"),(4,"未使用"),(5,"取消"),(6,"已核销"))


def otTypeChoices():
    dic = {}
    for d in otTypeDict.values():
        dic.update(d)
    return tuple(dic.items())

class special_calendar(models.Model):
    date = models.DateField(unique=True)
    date_type_choices=((1,"法定节假日"),(2,"调休"),(3,"特殊日期"))
    date_type = models.IntegerField()
    #emp_info_id = models.CharField(max_length=400,blank=True,null=True)#员工id的字符串拼接
    used_for = models.CharField(max_length=400,blank=True,null=True)
    """
    适用的范围
    如： '"gender":1,"group":"SetUp,Table","emp.id":"1,2,3"'
    """
    work_hours = models.IntegerField()#不可改变的
    work_hours_special = models.IntegerField(blank=True,null=True)
    #特殊日期的说明
    description = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        db_table = "special_calendar"

    def __str__(self):
        return "{} - {} - {} - {}".format(self.id,self.date,self.date_type,self.work_hours)

    def viewJson(self):
        return '"id":{},"date":"{}","dateType":"{}","range":"{}","wh":"{}","description":"{}"'.format(self.id,\
                self.date,dict(self.date_type_choices)[self.date_type],\
                json.loads(self.used_for) if self.used_for else "全体员工",\
                str(self.work_hours_special if self.work_hours_special else self.work_hours) + "小时",\
                self.description)
    
class emp_info(models.Model):
    emp_id = models.CharField(max_length=10,unique=True)
    name = models.CharField(max_length=10)
    name_pinyin = models.CharField(max_length=30)
    gender_choices=((1,"男"),(2,"女"))
    gender = models.SmallIntegerField(choices=gender_choices)
    password = models.CharField(max_length=20)
    department = models.CharField(max_length=10)
    dimission_choices=((0,"离职"),(1,"在职"))
    dimission = models.SmallIntegerField(choices=dimission_choices,default=1)
    email = models.CharField(max_length=100)
    EntryDate = models.DateField(blank=True,null=True) #入职日期 datetime.date

    class Meta:
        db_table = "emp_info"

    def empGroups(self):
        groups = self.group_rule_set.filter()
        if groups:
            group = groups.values("name")
            groupID = groups.values("id")
            gl = []
            glID = []
            for g in group:
                gl.append(g['name'])
            for gID in groupID:
                glID.append(gID['id'])
            groupName = gl
        else:
            groupName = [""]
            glID =[]

        return groupName,glID
    #groupAbbreviationDict
    def empMainGroup(self):
        gid = self.empGroups()[1]
        if len(gid)>1:
            for g in gid:
                if g == 1:
                    continue
                else:
                    mainGroup = groupAbbreviationDict[g]
                    break
        else:
            mainGroup = groupAbbreviationDict[gid[0]]
        return mainGroup

    def viewJson(self):
        groupName = ",".join(self.empGroups()[0])
        return '"id":{},"empID":"{}","name":"{}","name_pinyin":"{}","gender":"{}","department":"{}","email":"{}","group":"{}",'\
               '"dimission":"{}","EntryDate":"{}"'.format(self.id,self.emp_id,self.name,self.name_pinyin,dict(self.gender_choices)[self.gender],
                                       self.department,self.email,groupName,dict(self.dimission_choices)[self.dimission],self.EntryDate)

class group_rule(models.Model):
    emp_id = models.ManyToManyField('emp_info')
    name = models.CharField(unique=True,max_length=30)
    parent_id = models.IntegerField(blank=True,null=True)

    class Meta:
        db_table = "group_rule"
        
    def viewJson(self):
        return '"id":{},"name":"{}"'.format(self.id,self.name)

class role(models.Model):
    emp_id = models.ManyToManyField('emp_info')
    name = models.CharField(unique=True,max_length=30)

    class Meta:
        db_table = "role"
        
    def viewJson(self):
        return '"id":{},"name":"{}"'.format(self.id,self.name)

class function(models.Model):
    role_id = models.ManyToManyField('role')
    name = models.CharField(unique=True,max_length=30)
    fun_type_choices=((1,"List"),(2,"Button"))
    fun_type = models.SmallIntegerField(choices=fun_type_choices)
    explain = models.CharField(max_length=100)

    class Meta:
        db_table = "function"
        
    def viewJson(self):
        return '"id":{},"name":"{}","functionType":"{}",'\
               '"explain":"{}"'.format(self.id,self.name,dict(self.fun_type_choices)[self.fun_type],self.explain)

class day(models.Model):
    #emp_id = models.IntegerField()#员工信息表好了之后，要做成外键
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,to_field="emp_id",db_column="emp_id")
    date = models.DateField()
    st_om = models.TimeField(verbose_name="start time office manual",blank=True,null=True)
    st_os = models.TimeField(verbose_name="start time office system",blank=True,null=True)
    reason = models.CharField(max_length=30,blank=True,null=True)
    et_o = models.TimeField(verbose_name="end time office",blank=True,null=True)
    wh = models.IntegerField(verbose_name="work hours")#分钟，所以Int
    wh_o = models.IntegerField(verbose_name="work hours office",default=0)#分钟，所以Int
    wh_ot = models.IntegerField(verbose_name="work hours OT",default=0)#分钟，所以Int
    st_h = models.TimeField(verbose_name="start time home",blank=True,null=True)
    et_h = models.TimeField(verbose_name="end time home",blank=True,null=True)
    wh_h = models.IntegerField(verbose_name="work hours home",default=0)#分钟，所以Int
    st_h_path = models.FilePathField(max_length=200,blank=True,null=True)
    et_h_path = models.FilePathField(max_length=200,blank=True,null=True)
    ot_path = models.FilePathField(max_length=200,blank=True,null=True)
    ot_type_choices=((1,"不想回家"),(2,"补时长"),(3,"工作原因"))
    ot_type = models.SmallIntegerField(choices=ot_type_choices,default=None,blank=True,null=True)
    ot_reason = models.CharField(max_length=300,blank=True,null=True)

    class Meta:
        unique_together = ('emp_id','date',)
        db_table = "day"
    def viewJson(self):
        return '"id":{},"empID":"{}","date":"{}","startTimeOfficeManual":"{}","startTimeOfficeSystem":"{}",'\
               '"endTimeOffice":"{}","reason":"{}","workHoursLaw":{},"workHoursOffice":"{}","workHoursOT":"{}",'\
               '"startTimeHome":"{}","endTimeHome":"{}","workHoursHome":"{}","startTimeHomePath":"{}",'\
               '"endTimeHomePath":"{}","name":"{}","otPath":"{}","ot_type":"{}",'\
               '"ot_reason":"{}"'.format(self.id,self.emp_id.emp_id,self.date,self.st_om,self.st_os,self.et_o,
                                      self.reason,self.wh,pubFun.convertMinute(self.wh_o),pubFun.convertMinute(self.wh_ot),
                                      self.st_h,self.et_h,pubFun.convertMinute(self.wh_h),
                                      convertPath(self.st_h_path),convertPath(self.et_h_path),
                                      self.emp_id.name,convertPath(self.ot_path),self.ot_type,self.ot_reason)

class attendance_day(models.Model):
    emp_id = models.ForeignKey("emp_info", on_delete=models.CASCADE, to_field="emp_id", db_column="emp_id")
    date = models.DateField()
    first = models.TimeField(verbose_name="First In", blank=True, null=True)
    last = models.TimeField(verbose_name="Last Out", blank=True, null=True)
    wh = models.IntegerField(verbose_name="work hours")  # 分钟，所以Int

    class Meta:
        unique_together = ('emp_id', 'date',)
        db_table = "attendance_day"

    def viewJson(self):
        return '"id":{},"empID":"{}","date":"{}","firstIn":"{}",'\
               '"lastOut":"{}","workhours":{}'.format(self.id,\
                     self.emp_id.emp_id,self.date,self.first,self.last,self.wh)

class compoff(models.Model):
    emp_id = models.ForeignKey("emp_info", on_delete=models.CASCADE, to_field="emp_id", db_column="emp_id")
    date = models.DateField()
    compoff_type = models.SmallIntegerField(choices=compoff_type_choices)
    compoff_wh = models.IntegerField(verbose_name="compoff minutes") # 分钟，所以Int
    approve = models.SmallIntegerField(choices=compoff_approve_choices,default=0)#在家都是0
    status = models.SmallIntegerField(choices=compoff_status_choices,default=4)
    used_wh = models.IntegerField(verbose_name="used minutes",blank=True,null=True) # 分钟，所以Int

    class Meta:
        db_table = "compoff"

    def viewJson(self):
        return '"id":{},"empID":"{}","date":"{}","type":"{}",'\
               '"wh":"{}","approve":"{}","status":"{}","usedWH":"{}"'.format(self.id,\
                     self.emp_id.emp_id,self.date,dict(compoff_type_choices)[self.compoff_type],\
                     pubFun.convertMinute(self.compoff_wh),dict(compoff_approve_choices)[self.approve],\
                     dict(compoff_status_choices)[self.status],\
                     pubFun.convertMinute(self.used_wh) if self.used_wh else "")

class leave(models.Model):
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,to_field="emp_id",db_column="emp_id")
    date = models.DateField()#开始时间
    date_end = models.DateField()
    leave_type = models.SmallIntegerField(choices=leave_type_choices)
    leave_from = models.CharField(max_length=300)
    leave_days = models.FloatField()#天
    #leave_half_day_choices=((0,"全天"),(1,"上午"),(2,"下午"))
    #leave_half_day = models.SmallIntegerField(choices=leave_half_day_choices)
    duration_choices=((0,"全天"),(1,"上午"),(2,"下午"))
    """
    start_duration,end_duration统一，如果全天，为0，上午为1，下午为2
    """
    start_duration = models.SmallIntegerField(choices=duration_choices)
    end_duration = models.SmallIntegerField(choices=duration_choices)
    reason = models.CharField(max_length=30)
    approve = models.SmallIntegerField(choices=approve_choices,default=0)
    levNo = models.CharField(max_length=30,blank=True,null=True) #from ultimatix

    class Meta:
        #unique_together = ('emp_id','date','leave_type',)
        db_table = "leave"

    def viewJson(self):
        return '"id":{},"empID":"{}","startDate":"{}","endDate":"{}","leaveType":"{}","leave_days":"{}","reason":"{}",'\
               '"approve":"{}","name":"{}","leaveNo":"{}"'.format(self.id,self.emp_id.emp_id,self.date,self.date_end,
                    dict(leave_type_choices)[self.leave_type],str(self.leave_days)+"天",str(self.reason).replace("\""," "),
                    dict(approve_choices)[self.approve],self.emp_id.name,self.levNo)

class ot(models.Model):
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,
                               to_field="emp_id",db_column="emp_id",related_name='ot_emp_id')
    #related_name：可以用在反向查询时，省略_set
    date = models.DateField()
    start_time = models.TimeField()
    end_time = models.TimeField()
    ot_type_choices=otTypeChoices()
    #((1,"A1：新增需要、修改多"),(2,"A2：临时增加项目、需求或者修改"),(3,"A3：资料提供晚，拖延"),(4,"B1：效率低"),(5,"B2：正确率低"),(6,"C：协助其他组员，或者SPC项目"))
    ot_type = models.SmallIntegerField(choices=ot_type_choices)
    weekday_choices=((1,"是"),(2,"否"),(3,"节假日"),(4,"特殊日期"))
    weekday = models.SmallIntegerField(choices=weekday_choices)
    ot_hours = models.IntegerField()#分钟，所以Int
    reason = models.CharField(max_length=100)
    onl = models.CharField(max_length=20)
    meel_fee = models.FloatField()#models.IntegerField(default=0)
    taxi_fee = models.FloatField()#models.IntegerField(default=0)
    ot_request_date = models.DateField(blank=True,null=True)
    ot_request_time = models.TimeField(blank=True,null=True)
    ot_path = models.FilePathField(max_length=200,blank=True,null=True)
    approve = models.SmallIntegerField(choices=approve_choices)

    class Meta:
        #unique_together = ('emp_id','date',)
        db_table = "ot"

    def viewJson(self):
        return '"id":{},"empID":"{}","date":"{}","startTime":"{}","endTime":"{}","otType":"{}","weekday":"{}",'\
               '"otHours":"{}","reason":"{}","onlNo":"{}","meelFee":{},"taxiFee":{},"otRequest":"{}",'\
               '"otPath":"{}","approve":"{}","name":"{}"'.format(self.id,self.emp_id.emp_id,self.date,self.start_time,
                self.end_time,dict(self.ot_type_choices)[self.ot_type],dict(self.weekday_choices)[self.weekday],
                pubFun.convertMinute(self.ot_hours),str(self.reason).replace("\""," "),self.onl,self.meel_fee,
                self.taxi_fee,str(self.ot_request_date) + "~" + str(self.ot_request_time),convertPath(self.ot_path),
                dict(approve_choices)[self.approve],self.emp_id.name)

    def viewData(self):
        return '"id":%d,"empID":"%s","date":"%s","startTime":"%s","endTime":"%s","otType":"%s","weekday":%s,'\
               '"otHours":%f,"reason":"%s","onl":"%s","meelFee":%f,"taxiFee":%f,"otRequestDate":"%s","otRequestTime":"%s",'\
               '"otPath":"%s","approve":%d,"name":"%s"'%(self.id,self.emp_id.emp_id,self.date,
                pubFun.convertTime(self.start_time,"%H:%M"),pubFun.convertTime(self.end_time,"%H:%M"),
                dict(self.ot_type_choices)[self.ot_type],self.weekday,self.ot_hours/60,str(self.reason).replace("\""," "),
                self.onl,self.meel_fee,self.taxi_fee,self.ot_request_date,
                pubFun.convertTime(self.ot_request_time,"%H:%M"),convertPath(self.ot_path),
                self.approve,self.emp_id.name)


class account_leave(models.Model):#单位：天
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,to_field="emp_id",db_column="emp_id",unique=True)
    sl = models.FloatField(verbose_name="sick leave",default=12.5)
    sal = models.FloatField(verbose_name="Statutory Annual Leave",default=5)
    bal = models.FloatField(verbose_name="Benefit Annual Leave",default=10)
    lwp = models.FloatField(verbose_name="Leave Without Pay", default=0)

    class Meta:
        db_table = "account_leave"

    def viewJson(self):
        return '"id":{},"empID":"{}","sickLeave":{},"statAnnualLeave":{},'\
               '"beneAnnualLeave":{},"leaveWithoutPay":{},"name":"{}"'.format(self.id,\
                self.emp_id.emp_id,int(self.sl),int(self.sal),int(self.bal),int(self.lwp),self.emp_id.name)

class account_pay(models.Model):#单位：小时
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,to_field="emp_id",db_column="emp_id")
    year = models.IntegerField()
    month = models.IntegerField()
    wd_ot = models.FloatField(default=0)
    holiday_ot = models.FloatField(default=0)
    we_ot = models.FloatField(default=0)
    we_ot_lock_choices=((0,"未付费"),(1,"已付费"),(2,"被拒"))
    we_ot_lock = models.SmallIntegerField(choices=we_ot_lock_choices,default=0)

    class Meta:
        unique_together = ('emp_id','year','month',)
        db_table = "account_pay"

    def viewJson(self):
        return '"id":{},"empID":"{}","year":{},"month":{},"workDayOT":{},"holidayOT":{},'\
               '"weekEndOT":{},"weekEndOTLock":{},"name":"{}"'.format(self.id,\
                self.emp_id.emp_id,self.year,self.month,self.wd_ot,self.holiday_ot,\
                self.we_ot,self.we_ot_lock,self.emp_id.name)

class account_compoff(models.Model):#单位：分钟
    emp_id = models.ForeignKey("emp_info",on_delete=models.CASCADE,to_field="emp_id",db_column="emp_id",unique=True)
    compoff_home_wd = models.FloatField(default=0)
    compoff_home_wd2 = models.FloatField(default=0)
    compoff_office_wd = models.FloatField(default=0)
    compoff_office_we = models.FloatField(default=0)
    compoff_home1 = models.FloatField(default=0)
    compoff_home2 = models.FloatField(default=0)
    compoff_home3 = models.FloatField(default=0)
    compoff_office1 = models.FloatField(default=0)
    compoff_office2 = models.FloatField(default=0)
    compoff_office3 = models.FloatField(default=0)

    class Meta:
        db_table = "account_compoff"

    def viewJson(self):
        return '"id":{},"empID":"{}","workDayCompoffHome":{},"workDayCompoffOffice":{},'\
               '"weekEndCompoffOffice":{},"compoffHome1":{},"compoffHome2":{},"compoffHome3":{},'\
               '"compoffOffice1":{},"compoffOffice2":{},"compoffOffice3":{},"name":"{}"'.format(self.id,\
                self.emp_id.emp_id,self.compoff_home_wd,self.compoff_office_wd,\
                self.compoff_office_we,self.compoff_home1,self.compoff_home2,self.compoff_home3,\
                self.compoff_office1,self.compoff_office2,self.compoff_office3,self.emp_id.name)

def convertPath(path):
    if path:
        path = path[1:]
    return path

