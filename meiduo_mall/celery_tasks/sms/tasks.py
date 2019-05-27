from celery_tasks.main import celery_app


@celery_app.task
def cpp_send_sms_code(mobile, sms_code):
    """
    发送短信异步任务
    :param mobile: 手机号
    :param sms_code: 短信验证码
    :return:  成功0 失败1
    """
    from libs.yuntongxun.sms import CCP
    send_result = CCP().send_template_sms(mobile, [sms_code, 5], 1)
    return send_result



