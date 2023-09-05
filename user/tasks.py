from django.conf import settings
from blog_server.celery import app
from tools.sms import YunTongXin

# 发送随机码
@app.task
def send_sms_c(phone, code):
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
