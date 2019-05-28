import json
import re

from django import http
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
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
        login(request, user)

        #  namespace:name   主路由:子路由 注册成功，直接跳转到主页index
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', username, max_age=3600 * 24 * 15)
        return response


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


class LoginView(View):
    @staticmethod
    def get(request):

        return render(request, 'login.html')

    @staticmethod
    def post(request):
        """
        登陆界面提交表单 --- username password remembered--是否记住
        :param request:
        :return: HTML
        """
        #
        username = request.POST.get('username')
        password = request.POST.get('password')
        remembered = request.POST.get('remembered')

        # 不要相信前端 -- 还是要自己判断
        if not all([username, password]):
            return http.HttpResponseForbidden('参数不齐全')
        if not re.match(r'[a-zA-Z0-9_-]{5,20}', username):
            return http.HttpResponseForbidden('请输入5-20个字符的用户名')
        if not re.match(r'^[0-9a-zA-z]{8,20}$', password):
            return http.HttpResponseForbidden('请输入8-20位的密码')
        # 根据username ,password 获取当前的数据库中的账号对象 -- authenticate 是django 自带的
        from apps.users.utils import UsernameMobileAuthBackend
        user = UsernameMobileAuthBackend().authenticate(request, username, password)

        # 如果没有找到对应的账户，返回错误响应
        if user is None:
            return render(request, 'login.html', {'account_errmsg': '用户名或密码错误'})
        # 保持登陆状态
        login(request, user)

        # 判断是否需要记住账号
        if remembered == 'on':
            # 浏览器记住当前的账户
            request.session.set_expiry(None)
        else:
            # 关闭浏览器则过期
            request.session.set_expiry(0)

        # next ----http://www.meiduo.site:8000/login/?next=/info/
        # next 记录了用户未登录时访问的地址信息，可以帮助我们实现在用户登录成功后直接进入未登录时访问的地址

        next = request.GET.get('next')
        if next:
            response = redirect(next)
            response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
            return response

        # 三种方法用于显示首页的 用户名
        # 1 ajax 异步请求 -- 缺点： 需要网络，而且没什么意义
        # 2 通过 render 把 request.user 返回给前端，通过 jinja2 模板渲染 ---
        #       缺点： 不能静态化，后期要放到 nginx 上作为静态页面（因为访问量较大，所以静态化）
        # 3 通过 cookie 存储当前用户名，前端通过 getCookie 来获得 用户名 --- 当前使用
        response = redirect(reverse('contents:index'))
        response.set_cookie('username', user.username, max_age=3600 * 24 * 15)
        return response


class LogoutView(View):
    @staticmethod
    def get(request):
        # django封装的 退出功能 --- 删除的就是 session --- 退出就是不在保持回话状态
        logout(request)
        # 退出删除 cookie 中username的值 --- 看需求
        response = render(request, 'login.html')
        response.delete_cookie('username')
        return response


# 需要先判断是否登陆，如果没有登陆则跳转到登陆界面，如果登陆则跳转到用户中心
class UserinfoView(LoginRequiredMixin, View):
    # 使用了 LoginRequiredMixin 后，会自动的判断是否登陆 配置dev.py LOGIN_URL = '/login/'
    @staticmethod
    def get(request):
        context = {
            'username': request.user.username,
            'mobile': request.user.mobile,
            'email': request.user.email,
            'email_active': request.user.email_active,
        }
        return render(request, 'user_center_info.html', context=context)


from utils.views import LoginRequireJsonMixin

class EmailsView(LoginRequireJsonMixin, View):
    # LoginRequireJsonMixin 重写了父类 LoginRequiredMixin 中的 handle_no_permission 函数
    # handle_no_permission 这个函数再用户没有登陆时的处理，重写后返回json数据给前端
    @staticmethod
    def put(request):
        # 非表单提交方式
        # PUT提交方式 --- 是将数据放到 request.body 的 bytes 数据
        # 需要现转码成json的字符串，然后转成字典来提取
        json_str = request.body
        json_dict = json.loads(json_str)
        email = json_dict['email']

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return http.HttpResponseForbidden('参数email有误')

        request.user.email = email
        try:
            request.user.save()
        except Exception as e:
            logger.error(e)
            return http.JsonResponse({'code': RETCODE.DBERR, 'errmsg': '添加邮箱失败'})

        # 发送邮件

        return http.JsonResponse({'code': RETCODE.OK, 'errmsg': '添加邮箱成功'})
