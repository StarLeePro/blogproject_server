import json

from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views import View
from .models import UserProfile
import hashlib
import random
from tools.logging_dec import logging_check
from django.core.cache import cache
from tools.sms import YunTongXin
from django.conf import settings
from .tasks import send_sms_c


# 异常码 10100-10199

# django提供了一个装饰器 method_decorator 可以将函数的装饰器转换成方法的装饰器

# Create your views here.

# FBV
@logging_check
def users_views(request, username):
    if request.method != "POST":
        result = {'code': 10104, 'error': 'please use POST'}
        return JsonResponse(result)

    user = request.myuser
    avatar = request.FILES['avatar']
    user.avatar = avatar
    user.save()
    return JsonResponse({"code": 200})


# 定义视图类 CBV
# 更灵活，可继承
# 对未定义的http method请求，直接返回405响应
class UserViews(View):

    def get(self, request, username=None):

        if username:
            # /v1/users/lixing
            try:
                user = UserProfile.objects.get(username=username)
            except Exception as e:
                result = {'code': 10103, 'error': 'the username is wrong'}
                return JsonResponse(result)
            result = {'code': 200, 'username': username, 'data': {
                'info': user.info, 'sign': user.sign, 'nickname': user.nickname, 'avatar': str(user.avatar)
            }}
            return JsonResponse(result)
        else:
            # /v1/users
            pass

    def post(self, request):
        # 获取到的是json字符串
        json_str = request.body
        json_obj = json.loads(json_str)

        username = json_obj['username']
        email = json_obj['email']
        password_1 = json_obj['password_1']
        password_2 = json_obj['password_2']
        phone = json_obj['phone']
        sms_num = json_obj['sms_num']
        # 参数基本检查
        # 密码检查
        if password_1 != password_2:
            result = {"code": 10100, "error": "the password is not same"}
            return JsonResponse(result)
        # 电话号码格式检查
        if len(phone) != 11:
            result = {"code": 10101, "error": "the length of phone is wrong"}
            return JsonResponse(result)
        # 比对验证码是否正确
        old_code = cache.get('sms_%s' % (phone))
        if not old_code:  # 过期
            result = {'code': 10106, 'error': 'the code is wrong'}
            return JsonResponse(result)
        if int(sms_num) != old_code:  # 不一致
            result = {'code': 10106, 'error': 'the code is wrong'}
            return JsonResponse(result)

        # 检查用户名是否可用
        old_users = UserProfile.objects.filter(username=username)
        if old_users:
            result = {"code": 10102, "error": "the username is already existed"}
            return JsonResponse(result)
        # 在UserProfile表中新增数据（密码用md5储存
        p_m = hashlib.md5()
        p_m.update(password_1.encode())
        UserProfile.objects.create(username=username, nickname=username, password=p_m.hexdigest(), email=email,
                                   phone=phone)
        result = {'code': 200, 'username': username, 'data': {}}
        return JsonResponse(result)

    @method_decorator(logging_check)
    def put(self, request, username=None):
        # 更新用户信息[昵称，个人签名，个人描述]
        # 前端数据
        json_str = request.body
        json_obj = json.loads(json_str)
        # 根据姓名查找该用户

        user = request.myuser
        # 修改
        user.sign = json_obj['sign']
        user.info = json_obj['info']
        user.nickname = json_obj['nickname']

        user.save()
        return JsonResponse({'code': 200})


# 发送验证码
def sms_view(request):
    if request.method != 'POST':
        result = {'code': 10105, 'error': 'please use post'}
        return JsonResponse(result)
    json_str = request.body
    json_obj = json.loads(json_str)
    phone = json_obj['phone']

    # 生成随机码
    code = random.randint(1000, 9999)
    print('phone:', phone, 'code:', code)
    # 存储随机码 使用django-redis
    # pip3 install django-redis
    cache_key = 'sms_%s' % (phone)
    # 防抖，检查是否有发过未过期的验证码
    old_code = cache.get(cache_key)
    if old_code:
        return JsonResponse({'code': 10109, 'error': 'the code is already existed'})
    # 存到redis
    cache.set(cache_key, code, 60)
    # 发送随机码，短信
    # 存在一个第三方服务器崩溃的问题
    # 使用生产者消费者模型
    # django是生产者，将消费者工作，即一些可能存在阻塞的任务（脏累活）交给其他机器来处理
    # 解决方案：任务调度系统 celery
    send_sms_c.delay(phone, code)
    # 普通版
    # send_sms(phone, code)
    return JsonResponse({'code': 200})


# 发送随机码
def send_sms(phone, code):
    config = {
        # accountSid, accountToken, appId, templateId
        'accountSid': settings.ACCOUNTSID,
        'accountToken': settings.ACCOUNTTOKEN,
        'appId': settings.APPID,
        'templateId': settings.TEMPLATEID
    }
    yun = YunTongXin(**config)  # 双星号字典传参
    res = yun.run(phone, code)
    return res
