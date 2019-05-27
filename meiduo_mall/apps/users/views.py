import re

from django import http
from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View
from django_redis import get_redis_connection

from apps.users.models import User
from meiduo_mall.settings.dev import logger
from utils.response_code import RETCODE


class RegisterView(View):
    @staticmethod
    def get(request):
        """
        请求注册页面
        :param request:
        :return: render()
        """
        return render(request, 'register.html')

    @staticmethod
    def post(request):
        """
        提交表单时的逻辑
        :param request:
        :return: redirect(index.html) or render(register.html)
        """
        # 注册时的表单数据接受和判定
        username = request.POST.get('username')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        # 电话号码
        mobile = request.POST.get('mobile')
        # 短信验证吗
        sms_code = request.POST.get('sms_code')
        # 协议是否勾选
        allow = request.POST.get('allow')

        # 前段已经对注册的数据进行过校验--是否符合规则，如果后台校验失败，代表是非正常途径传过来的数据，直接禁止掉
        if not all([username, password, password2, mobile, sms_code, allow]):
            return http.HttpResponseForbidden('缺少必传参数')
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9a-zA-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        if password != password2:
            return http.HttpResponseForbidden('请输入8-20位的密码')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.HttpResponseForbidden('请输入正确的手机号码')
        # 协议选中 前端会给个值 on
        if allow != 'on':
            return http.HttpResponseForbidden('请勾选用户协议')

        # 提交数据后对段兴验证码进行判断 --- 不需要对 图形验证码进行判断，只有图形验证码输入这个你却才可以发短信
        sms_client = get_redis_connection('sms_code')
        ret_code = sms_client.get('%s' % mobile)
        if ret_code is None:
            return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'})
        if ret_code.decode() != sms_code:
            # 用 render 会直接刷新页面导致前面的数据无法再用，导致浪费,而且用户体验不好
            # 当输入错误时，应该只显示错误信息，不刷新页面
            return render(request, 'register.html', {'sms_code_errmsg': '短信验证码输入错误'})
        # 验证成功删除当前redis中的对应数据 --- 可能导致错误
        sms_client.delete('%s' % mobile)

        # 为了测试方便，先不存入数据库
        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            # logger.error(e)
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # django内部封装的login(),可以保持会话状态
        from django.contrib.auth import login
        login(request, user)

        #  namespace:name   主路由:子路由 注册成功，直接跳转到主页index
        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    @staticmethod
    def get(request, username):
        """
        验证用户名是否重复
        :param request:
        :param username:用户名
        :return: 'code':'','errmsg':'','count':
        """
        # if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
        #     return http.HttpResponseForbidden('请输入5-20个字符的用户名')

        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    @staticmethod
    def get(request, mobile):
        """
        验证手机号是否重复
        :param request:
        :param mobile:手机号码
        :return: 'code':'','errmsg':'','count':
        """
        # if not re.match(r'^1[3-9]\d{9}$', mobile):
        #     return http.HttpResponseForbidden('请输入正确的手机号码')
        # url的正则已经算是校验了
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})

# 错误，在表单提交之后执行的
# class SMSCheckView(View):
#     @staticmethod
#     def get(request):
#         sms_code = request.POST.get('sms_code')
#         mobile = request.POST.get('mobile')
#
#         # 提交数据后对段兴验证码进行判断 --- 不需要对 图形验证码进行判断，只有图形验证码输入这个你却才可以发短信
#         sms_client = get_redis_connection('sms_code')
#         ret_code = sms_client.get('%s' % mobile)
#         if ret_code is None:
#             # return render(request, 'register.html', {'sms_code_errmsg': '无效的短信验证码'}
#             return http.JsonResponse(content={'code': RETCODE.SMSCODERR, 'errmsg': '无效的短信验证码'})
#         if ret_code.decode() != sms_code:
#             # 用 render 会直接刷新页面导致前面的数据无法再用，导致浪费,而且用户体验不好
#             # 当输入错误时，应该只显示错误信息，不刷新页面
#             # return render(request, 'register.html', {'sms_code_errmsg': '短信验证码输入错误'})
#             return http.JsonResponse(content={'code': RETCODE.SMSCODERR, 'errmsg': '短信验证码输入错误'})
#         sms_client.delete('%s' % mobile)
#         return http.JsonResponse(content={'code': RETCODE.OK, 'errmsg': 'ok'})
