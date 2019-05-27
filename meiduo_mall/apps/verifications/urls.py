
from django.conf.urls import url
from . import views

urlpatterns = [
    # 图片验证码的子url
    url(r'^image_codes/(?P<uuid>[\w-]+)/$', views.ImageCodeView.as_view(), name='imagecode'),
    # 短信验证码的子url -- 有两种参数 1.url传参 2.查询参数传参
    url(r'^sms_codes/(?P<mobile>1[3-9]\d{9})/$', views.SMSCodeView.as_view(), name='smscode'),
]
