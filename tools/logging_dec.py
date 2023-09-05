from django.http import JsonResponse
import jwt
from django.conf import settings
from user.models import UserProfile

def logging_check(func):

    def wrap(request, *args, **kwargs):
        # 获取token request.META.get('HTTP_AUTHORIZATION')
        token = request.META.get("HTTP_AUTHORIZATION")
        if not token:
            result = {'code':403, 'error':'please login'}
            return JsonResponse(result)

        # 校验
        try:
            # algorithms='HS256'
            res = jwt.decode(token, settings.JWT_TOKEN_KEY)
        except Exception as e:
            print('jwt decode error is %s'%(e))
            result = {'code': 403, 'error': 'please login'}
            return JsonResponse(result)
        # 失败，返回code 403 error：please login

        # 获取登录用户
        username = res['username']
        user = UserProfile.objects.get(username=username)
        request.myuser = user # 将校验成功的user返回给视图函数

        return func(request, *args, **kwargs)
    return wrap

def get_user_by_request(request):
    # 尝试性的获取登录用户
    # return UserProfile obj
    token = request.META.get("HTTP_AUTHORIZATION")
    if not token:
        return None
    try:
        res = jwt.decode(token, settings.JWT_TOKEN_KEY)
    except Exception as e:
        return None
    username = res['username']
    user = UserProfile.objects.get(username=username)
    return user

