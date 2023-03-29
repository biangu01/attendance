from apscheduler.schedulers.background import BackgroundScheduler
from django_apscheduler.jobstores import DjangoJobStore, register_job
from . import pubFun,dbfun,log
import datetime
from django.views.decorators.csrf import csrf_exempt
from dbModel.models import account_leave,account_pay,account_compoff,compoff

scheduler = BackgroundScheduler()
scheduler.add_jobstore(DjangoJobStore(), "default")

# 时间间隔3秒钟打印一次当前的时间
#@register_job(scheduler, "interval", seconds=3, id='test_job')
#def my_job():
#    print("我是apscheduler任务")
"""
装饰器：@register_job
如：@register_job(scheduler, 'cron', id='test', hour=8, minute=30，args=['test'])
-scheduler: 指定调度器
-trigger: 任务执行的方式，共有三种： 'date'、'interval'、'cron'。
  date：实现单次任务  @register_job(scheduler, 'date', id='test', run_date='2019-07-07 22:49:00')
  interval：实现间隔性任务 @register_job(scheduler, 'interval', id='test', hours=3, minutes=30) 每隔3个半小时执行任务
  core：实现cron类的任务 @register_job(scheduler, 'cron', id='test', hour=8, minute=30) 每天8点半执行
-id: 任务的名字，不传的话会自动生成。不过为了之后对任务进行暂停、开启、删除等操作，
     建议给一个名字。并且是唯一的，如果多个任务取一个名字，之前的任务就会被覆盖。
-args: list类型。执行代码所需要的参数。
-next_run_time：datetime类型。开始执行时间。如果你现在创建一个定时任务，想3天后凌晨三点半自动给你女朋友发微信，那就需要这个参数了。
其他参数查源码
"""

#每月1号将3个月的数据更新一下 一个是account_compoff中的两个，一个是account_pay中的一个
"""
1、 找到所有的未离职的人
2、 按当月的月份，修改三个月前的信息
 account_compoff : 清空前三个的值，后六个带1，2，3的按月推迟
 account_pay : 新建一个月的，将三个月前的loct锁定
"""
#@register_job(scheduler, "cron", day=1,hour=0,minute=30, id='updateDBTask')
@register_job(scheduler, "cron", day=1,hour=0,minute=30, id='updateDBTask',replace_existing=True)
def updateDBTask():
    print("月更新任务开始")
    log.recourdLog("每月定时任务开始")
    emps = dbfun.findEmps(dimission=1)

    today = datetime.datetime.now()

    #used for test
    #today = datetime.datetime.strptime("2021-04-01", "%Y-%m-%d")
    #print(today,type(today))

    for emp in emps:
        #新建一个月的account_pay
        #！！！！！！！！！！！！！！需要考虑离职
        dbfun.addDB(account_pay,task=True,emp_id=emp,year=today.year,month=today.month)
        #将三个月前的loct锁定

        m = today.month - 3
        if m <0:
            year = today.year - 1
            m = 12 + m
        else:
            year = today.year
        ap = dbfun.searchDB(account_pay,emp_id=emp,year=year,month=m).first()
        if ap:
            if ap.we_ot_lock != 2:
                lock = ap.we_ot_lock
                ap.we_ot_lock = 1
                dbfun.updateDB(ap,{"lock":lock},{"lock":1},task=True)

        #account_compoff : 清空前三个的值，后六个带1，2，3的按月推迟
        ac = dbfun.searchDB(account_compoff,emp_id=emp).first()
        if ac:
            dicOri = {}
            dicNew = {}
            ac.compoff_home_wd2 = pubFun.compUpdate(dicOri, dicNew, "compoffHomeWeekDay2", ac.compoff_home_wd2, ac.compoff_home_wd)
            ac.compoff_home_wd = pubFun.compUpdate(dicOri, dicNew, "compoffHomeWeekDay", ac.compoff_home_wd, 0)
            ac.compoff_office_wd = pubFun.compUpdate(dicOri, dicNew, "compoffOfficeWeekDay", ac.compoff_office_wd, 0)
            ac.compoff_office_we = pubFun.compUpdate(dicOri, dicNew, "compoffOfficeWeekEnd", ac.compoff_office_we, 0)
            ac.compoff_home3 = pubFun.compUpdate(dicOri, dicNew, "compoffHome3", ac.compoff_home3, ac.compoff_home2)
            ac.compoff_home2 = pubFun.compUpdate(dicOri, dicNew, "compoffHome2", ac.compoff_home2, ac.compoff_home1)
            ac.compoff_home1 = pubFun.compUpdate(dicOri, dicNew, "compoffHome1", ac.compoff_home1, 0)
            ac.compoff_office3 = pubFun.compUpdate(dicOri, dicNew, "compoffOffice3", ac.compoff_office3, ac.compoff_office2)
            ac.compoff_office2 = pubFun.compUpdate(dicOri, dicNew, "compoffOffice2", ac.compoff_office2, ac.compoff_office1)
            ac.compoff_office1 = pubFun.compUpdate(dicOri, dicNew, "compoffOffice1", ac.compoff_office1, 0)

            dbfun.updateDB(ac, dicOri,dicNew, task=True)


    print("account_pay,_compoff月任务更新完毕")
    print(datetime.datetime.now())
    return pubFun.returnMsg(200)

"""
任务报错：Error getting due jobs from job store 'default':(0, '')
不知道原因
"""

@register_job(scheduler, "cron", hour=9,minute=20, id='updateCompoffTask',replace_existing=True)
def updateCompoffTask():
    print("每日倒休更新任务开始")
    log.recourdLog("每日倒休更新任务开始")
    #查找对应的几个月前（前一天）的日期
    today = datetime.datetime.now()
    # delta = datetime.timedelta(days=1)
    # today = today + delta*90

    m2_str = pubFun.dayBeforeMonth(today, 2, 2)
    m3_str = pubFun.dayBeforeMonth(today, 3, 2)

    #根据日期将当天的倒休状态改成过期
    #查找倒休的状态为可用的，日期小于m2和m3的对应类型的
    #com3 = dbfun.searchDB(compoff, date__lt=m3_str, status__range=[2, 4]).exclude(compoff_type=3)
    com36 = dbfun.searchDB(compoff, date__lt=m3_str, status__range=[2, 4], compoff_type__lt=3)
    com31 = dbfun.searchDB(compoff, date__lt=m3_str, status__range=[2, 4], compoff_type__gt=3)
    com2 = dbfun.searchDB(compoff, date__lt=m2_str, status__range=[2, 4], compoff_type=3)
    # from django.db.models.query import QuerySet
    # print(isinstance(com36, QuerySet))
    # print(isinstance(com31, QuerySet))
    # print(isinstance(com2, QuerySet))
    # if com36:
    #     print(type(com36),len(com36),com36.first())
    #     print(com36.first()._meta.db_table)
    # if com31:
    #     print(type(com31), len(com31), com31.first())
    #     print(com31.first()._meta.db_table)
    # if com2:
    #     print(type(com2), len(com2), com2.first())
    #     print(com2.first()._meta.db_table)
    #print("com2"+ str(len(com2)),";;;;com3"+str(len(com3)))
    # for c2 in com2:
    #     c2.status = 1
    #
    # for c3 in com3:
    #     if c3.compoff_type < 3:
    #         c3.status = 6
    #     else:
    #         c3.status = 1
    if com2:
        print("2",type(com2), len(com2), com2.first())
        dbfun.updateDB(com2, dicOri={"comoff2": "Ori"}, dicNew={"comoff2": "过期"},task=True, **{"status": 1})
    if com36:
        print("36",type(com36), len(com36), com36.first())
        dbfun.updateDB(com36, dicOri={"comoff3": "Ori"}, dicNew={"comoff3": "核销"}, task=True, **{"status": 6})
    if com31:
        print("31",type(com31), len(com31), com31.first())
        dbfun.updateDB(com31, dicOri={"comoff3": "Ori"}, dicNew={"comoff3": "过期"}, task=True, **{"status": 1})

    print("********************************************")
    print("每日倒休更新任务结束")
    print(datetime.datetime.now())
    log.recourdLog("每日倒休更新任务结束")
    return pubFun.returnMsg(200)

#1月1号和7月1号更新所有人的账户信息，主要是法定年假和福利年假 -- 这个可以考虑用传excel的方式修改，因为不确定

scheduler.start()

def runupdateDBTask(request):
    updateDBTask()
    return pubFun.returnMsg(200,"done")
