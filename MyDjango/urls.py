"""MyDjango URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.conf.urls import url

from . import dbfun,dayInOffice,day,login,readExcel,upload
from . import dayInHome,leave,ot,search,account,emp,searchEmp,month
from . import log,holiday,password,task,download,test,view
from . import sendEmail,compoff

urlpatterns = [
    path('admin/', admin.site.urls),
    path('addHoliday/',dbfun.addHoliday),#use only once
    path('test/',test.test),#for my test
    path('ces/',dbfun.find),
    path('dayInOffice',dayInOffice.day_office),
    path('calendarDay',day.calendarDay),
    path('calendarDay1',day.calendarDay1),
    path('searchDay',day.searchDay),
    path('login',login.login),
    path('dayInHome',dayInHome.day_home),
    path('leaveApply',leave.leave_apply),
    path('otApply',ot.ot_apply),
    path('searchList',search.emp_view),
    path('cancelOT',ot.ot_cancel),
    path('findOT',ot.findOT),
    path('cancelLeave',leave.leave_cancel),
    path('leaveDate',leave.search_leave_days),
    path('approveOT',ot.ot_approve),
    path('approveLeave',leave.leave_approve),
    path('uploadFile',upload.uploadFile),
    path('addEmp',emp.addEmp),
    path('searchEmp',searchEmp.search_emp),
    path('cancelDay',search.cancelDay),
    path('otType',ot.otType),
    path('findAllEmps',emp.findAllEmps),
    path('getEmp',emp.getEmpInfo),
    path('groups',emp.findGroup),
    path('updateEmp',emp.updateEmp),
    path('setHoliday',holiday.setHoliday),
    path('getHolidays',holiday.findSpecialHoliday),
    path('download',download.download),
    path('checkDayInfo',day.checkDayInfo),
    path('matchData',view.matchData),
    path('findAttendance',view.findAttendance),
    path('runupdateDBTask',task.runupdateDBTask),#用于手动更新每月任务
    path('findCompoff',compoff.findCompoff),
    path('searchApprove',search.emp_view_Approve),
    url(r'showReminder/(?P<reName>\w+)/$',view.showReminder),
]
