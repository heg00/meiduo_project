from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from . import constants

"""图形验证码"""


class ImageCodeView(View):
    @staticmethod
    def get(request, uuid):
        """

        :param request:
        :param uuid:唯一标识图形验证码所属于的用户
        :return:image/jpg:返回图片数据
        """
        from libs.captcha import captcha
        # return : string, bytes/StringIO.value
        text, image = captcha.captcha.generate_captcha()
        from django_redis import get_redis_connection
        redis_client = get_redis_connection('verify_image_code')
        redis_client.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)
        # HttpResponse中的content接受的是 bytes
        return http.HttpResponse(content_type='image/jpg', content=image)
