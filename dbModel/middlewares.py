from django.utils.deprecation import MiddlewareMixin
from MyDjango import log,pubFun
import traceback

class testException(MiddlewareMixin):
    def process_request(self, request):
        #print("1. My test middlewares - process_request")
        pass

    def process_response(self, request, response):
        #print("2. My test middlewares - process_response")
        return response

    def process_view(self,request, view_func, view_args, view_kwargs):
        #print("3. md1  process_view 方法！") #在视图之前执行 顺序执行
        #return view_func(request)
        pass


    def process_exception(self, request, exception):#引发错误 才会触发这个方法
        log.recourdErrorLog(str(request) + ";" + traceback.format_exc())
        return pubFun.returnMsg(208,"系统错误,技术人员正在努力调试中...")
        # return HttpResponse(exception) #返回错误信息
