import datetime
import hashlib
import base64
import json
import random

import requests


class YunTongXin():
    base_url = 'https://app.cloopen.com:8883'

    def __init__(self, accountSid, accountToken, appId, templateId):
        self.accountSid = accountSid  # 账号id
        self.accountToken = accountToken  # 授权令牌
        self.appId = appId # 应用id
        self.templateId = templateId # 模版id
    def get_request_url(self, sig):
        # 业务url /2013-12-26/Accounts/{accountSid}/SMS/{funcdes}?sig={SigParameter}
        self.url = self.base_url + '/2013-12-26/Accounts/%s/SMS/TemplateSMS?sig=%s' % (self.accountSid, sig)
        return self.url

    def get_timestamp(self):
        # 生成时间戳
        return datetime.datetime.now().strftime('%Y%m%d%H%M%S')

    def get_sig(self, timestamp):
        # 生成业务url中的sig
        s = self.accountSid + self.accountToken + timestamp
        m = hashlib.md5()
        m.update(s.encode())
        return m.hexdigest().upper()

    def get_request_header(self, timestamp):
        # 生成请求头
        s = self.accountSid + ':' + timestamp
        auth = base64.b64encode(s.encode()).decode()
        return {
            'Accept': 'application/json',
            'Content-Type': 'application/json;charset=utf-8',
            'Authorization': auth
        }
    def get_request_body(self, phone, code):
        # appid 2c94811c8a27cf2d018a3bb6a07106bf
        return {
            'to': phone,
            'appId': self.appId,
            'templateId': self.templateId,
            'datas': [code, "3"],  # 三分钟
        }


    def request_api(self, url, header, body):
        # 发送post请求
        res = requests.post(url, headers=header, data=body)
        return res.text  # 拿到响应内容
    # 测试
    def run(self, phone, code):  # code仅支持四位数字
        # 获取时间戳
        timestamp = self.get_timestamp()
        # 生成签名
        sig = self.get_sig(timestamp)
        # 生成业务url
        url = self.get_request_url(sig)
        # print(url)
        header = self.get_request_header(timestamp)
        # print(header)
        # 生成请求体
        body = self.get_request_body(phone, code)
        # 发请求
        data = self.request_api(url, header, json.dumps(body))
        return data


