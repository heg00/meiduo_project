from celery import Celery

# 当前文件是入口文件，启动celery 时启动这个文件就行

import os
# 以防使用 django 的包时找不到
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "meiduo_mall.settings.dev")

# 1 实例化 app -- celery_app  params : 当前功能的目录名
celery_app = Celery('celery_tasks')
# 2 设置配置 --- celery_tasks.config --- 这是使用配置文件导入
celery_app.config_from_object('celery_tasks.config')
# 3 自动寻找任务 -- 主要是寻找 sms 包下的 tasks.py 文件 ---
# 注意 tasks.py 文件名不能更改
celery_app.autodiscover_tasks(['celery_tasks.sms'])
celery_app.autodiscover_tasks(['celery_tasks.email'])




