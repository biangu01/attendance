# -*- coding: UTF-8 -*-
import logging,os
from . import constants

"""
%(levelno)s：打印日志级别的数值
%(levelname)s：打印日志级别的名称
%(pathname)s：打印当前执行程序的路径，其实就是sys.argv[0]
%(filename)s：打印当前执行程序名
%(funcName)s：打印日志的当前函数
%(lineno)d：打印日志的当前行号
%(asctime)s：打印日志的时间
%(thread)d：打印线程ID
%(threadName)s：打印线程名称
%(process)d：打印进程ID
%(message)s：打印日志信息
"""
"""
级别  对应的值
CRITICAL    50
ERROR   40
WARNING 30 
INFO    20
DEBUG   10
NOTSET  0
"""
jsonformat = '{"type":"%(levelname)s","systemtime":"%(asctime)s","message":"%(message)s","thread":"%(thread)d","process":"%(process)d"},'

def recourdLog(message):
    logger = logging.getLogger(__name__)
    logger.setLevel(level=logging.INFO)
    path = constants.LOGGER_INFO_PATH
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)
    if not logger.handlers:
        #%(asctime)s - %(message)s - %(name)s - %(levelname)s - %(thread)d - %(process)d
        handler = logging.FileHandler(path + constants.LOGGER_INFO_FILENAME,encoding='utf-8')
        handler.setLevel(logging.INFO)
        #这里可以改成JSON的格式，后面就可以直接用了
        formatter = logging.Formatter(jsonformat)
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    logger.info(message)

def test(request):
    empID = request.GET['id']
    date = request.GET['date']
    from dbModel.models import account_pay,emp_info,special_calendar
    from . import dbfun,pubFun,day
    emp = dbfun.searchDB(emp_info,emp_id=empID).first()
    
    return pubFun.returnMsg(201,day.dateInfo(date,True,emp))

def recourdErrorLog(message):
    loggerError = logging.getLogger("MyDjango-Error")
    loggerError.setLevel(level=logging.ERROR)
    path = constants.LOGGER_ERROR_PATH
    if os.path.exists(path):
        pass
    else:
        os.makedirs(path)
    if not loggerError.handlers:
        handler = logging.FileHandler(path + constants.LOGGER_ERROR_FILENAME,encoding='utf-8')
        handler.setLevel(logging.ERROR)
        #这里可以改成JSON的格式，后面就可以直接用了
        formatter = logging.Formatter(jsonformat)
        handler.setFormatter(formatter)
        loggerError.addHandler(handler)
    loggerError.error(message)
