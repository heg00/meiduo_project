import re

from django import http
from django.contrib.auth import login
from django.db import DatabaseError
from django.shortcuts import render, redirect
from django.urls import reverse
from django.views import View

from apps.users.models import User
from utils.response_code import RETCODE


class RegisterView(View):
    @staticmethod
    def get(request):
        return render(request, 'register.html')

    @staticmethod
    def post(request):
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

        # 前段已经对注册的数据进行过校验，如果后台校验失败，代表是非正常途径传过来的数据，直接禁止掉
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

        try:
            user = User.objects.create_user(username=username, password=password, mobile=mobile)
        except DatabaseError:
            return render(request, 'register.html', {'register_errmsg': '注册失败'})
        # django内部封装的login(),可以保持会话状态
        # from django.contrib.auth import login
        login(request, user)
        #  namespace:name   主路由:子路由 注册成功，直接跳转到主页index
        return redirect(reverse('contents:index'))


class UsernameCountView(View):
    @staticmethod
    def get(request, username):
        count = User.objects.filter(username=username).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})


class MobileCountView(View):
    @staticmethod
    def get(request, mobile):
        count = User.objects.filter(mobile=mobile).count()
        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': 'OK', 'count': count})
