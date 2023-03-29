import hashlib #1，首先引入hashlib模块
import base64
from . import pubFun

def password_encrypt(pwd):
    md5 = hashlib.md5()# 2，实例化md5() 方法
    md5.update(pwd.encode()) # 3，对字符串的字节类型加密
    result = md5.hexdigest() # 4，加密
    return result

def test(request):
    password = request.GET.get("password","")
    #key = "1234567890abcdefghijklmnopqrstuvwxyz"
    passwordencode = password.encode(encoding="utf-8")
    print(passwordencode)
    encode = base64.b64encode(passwordencode)
    print(encode)
    ###################################
    decode = base64.b64decode(encode)
    passworddecode = decode.decode()
    print(passworddecode)
    md5 = password_encrypt(passworddecode)
    print(md5, len(md5))
    return pubFun.returnMsg(201,md5)