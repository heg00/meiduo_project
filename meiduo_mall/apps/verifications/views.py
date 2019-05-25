from django import http
from django.shortcuts import render

# Create your views here.
from django.views import View

from . import constants

"""图形验证码"""

#  /????????不理解
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
        # text 应该是根据图片的不同二生成的图片 标志
        text, image = captcha.captcha.generate_captcha()
        from django_redis import get_redis_connection
        # get_redis_connection 返回一个redis的链接客服端
        redis_client = get_redis_connection('verify_image_code')
        # setex(存储在redis中的key,过期时间(5*60),存储在redis中的key对应的value)
        redis_client.setex('img_%s' % uuid, constants.IMAGE_CODE_REDIS_EXPIRES, text)

        # HttpResponse中的content接受的是 bytes
        return http.HttpResponse(content_type='image/jpg', content=image)
