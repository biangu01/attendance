from dbModel.models import special_calendar
import datetime,calendar
from . import pubFun,day

#当月应上班时长
def whMonthStatutory(year,month,dayV=None,emp=None,nineHourOneDay=None):
    #today = datetime.date.today()
    if dayV:
        days = dayV
    else:
        days = calendar.monthrange(year,month)[1]
        
    total = 0
    for d in range(1,days+1):
        day_ = str(year) + "-" +str(month) + "-" + str(d)
        h = day.dateInfo(day_,emp=emp)[1]
        if nineHourOneDay:
            h = h+1 if h>4 else h
        total += h

    return total
    