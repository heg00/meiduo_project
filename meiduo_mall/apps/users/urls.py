
from django.conf.urls import url
from . import views

urlpatterns = [
    # 注册页面
    url(r'^register/$', views.RegisterView.as_view(), name='register'),
    # axios -- 判断用户名是否重复（账号是否已存在）
    url(r'^usernames/(?P<username>[a-zA-Z0-9_-]{5,20})/count/$', views.UsernameCountView.as_view()),
    # axios -- 判断手机号是否重复
    url(r'^mobiles/(?P<mobile>1[3-9]\d{9})/count/$', views.MobileCountView.as_view()),
    # 登陆界面
    url(r'^login/$', views.LoginView.as_view()),
    # 用于表单提交时检查 smscode是否正确，不刷新页面
    # url(r'^sms/$', views.SMSCheckView.as_view()),
]
