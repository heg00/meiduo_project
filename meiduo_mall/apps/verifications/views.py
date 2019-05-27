import random

from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View
from django_redis import get_redis_connection

from libs.yuntongxun.sms import CCP
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE
from . import constants


class ImageCodeView(View):
    @staticmethod
    def get(request, uuid):
        """
        生成验证码图片，并将标示存入redis中，然后返回给前端
        前端根据 uuid 组成的 url 访问 get(request,uuid)时，会直接现生成一个 image,然后讲 image 的二进制文件返回
        :param request:
        :param uuid:唯一标识图形验证码所属于的用户
        :return:image/jpg:返回图片数据
        """
        from libs.captcha import captcha
        # return : string, bytes/StringIO.value
        # text 是图片验证码的值，校验的时候需要用
        text, image = captcha.captcha.generate_captcha()
        # get_redis_connection 返回一个redis的链接客服端
        redis_client = get_redis_connection('verify_image_code')
        # setex(存储在redis中的key,过期时间(5*60),存储在redis中的key对应的value)
        redis_client.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # HttpResponse中的content接受的是 bytes
        return http.HttpResponse(content_type='image/jpg', content=image)


class SMSCodeView(View):
    # this.host + '/sms_codes/' + this.mobile + '/?image_code=' + this.image_code + '&image_code_id=' + this.image_code_id;
    @staticmethod
    def get(request, mobile):
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('image_code_id')
        # 1. 先判断图形验证码是否对，不对的话返回错误信息
        # 1.1 链接redis,查询验证码，  --- redis 中拿出的数据是 bytes 类型的
        # 1.2 查到了拿出数据用于对比并删除数据库中的数据
        # 1.3 没查到直接返回信息

        image_client = get_redis_connection('verify_image_code')
        code = image_client.get('img_%s' % uuid)
        # 判断是否过期
        if code is None:
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码已过期'})
        # 删除数据库中数据---已经拿到数据了
        image_client.delete('img_%s' % uuid)
        # 判断验证码是否正确
        if code.decode().lower() != image_code.lower():
            return http.JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '验证码输入错误'})

        # 2. 生成对应的 sms_code，存入到redis中，并通过 荣连云 向对应的手机号发送短信

        sms_client = get_redis_connection('sms_code')

        # 2.1 校验当前redis中对应发送标致是否存在，存在则信息发送过于频繁
        send_flag = sms_client.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': RETCODE.THROTTLINGERR, 'errmsg': '发送短信过于频繁'})

        smscode = '%06d' % random.randint(0, 999999)
        # 2.2 发送短信给 mobile 用户
        # CCP().send_template_sms(mobile, [smscode, 5], 1)
        # 使用 celery 异步发送短信
        from celery_tasks.sms.tasks import cpp_send_sms_code
        cpp_send_sms_code.delay(mobile, smscode)
        # 创建redis 的 pipeline, 提高服务器的执行效率
        pl = sms_client.pipeline()
        # 2.3 将 mobile 当做唯一标识符 key 来存储 sms_code（短信验证码）
        pl.setex(mobile, constants.SMS_CODE_REDIS_EXPIRES, smscode)
        # 2.4 添加当前smscode 的存在标致，防止信息发送过于频繁
        pl.setex('send_flag_%s' % mobile, constants.SEND_SMS_CODE_INTERVAL, 1)
        pl.execute()
        return http.JsonResponse({'code': '0', 'errrmsg': '信息发送成功'})
