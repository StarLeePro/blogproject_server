# 消费者
from celery import Celery
from django.conf import settings
import os


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'blog_server.settings')

app = Celery('blog_server')
app.conf.update(
    BROKER_URL = 'redis://:Lx18794640447@127.0.0.1:6379/1'
    # BROKER_URL = 'redis://127.0.0.1:6379/1'
)

# 自动去注册应用下寻找加载worker函数
app.autodiscover_tasks(settings.INSTALLED_APPS)