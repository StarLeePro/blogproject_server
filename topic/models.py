from django.db import models
from user.models import UserProfile
# Create your models here.

# 后端给前端文章全部内容，前端自己截取  不可行
# 后端从数据库中获取全部文章内容，截取好之后响应给前端   省带宽  不可行
# 数据库冗余一个字段【简介】，后端只取简介字段内容

class Topic(models.Model):

    title = models.CharField(max_length=50, verbose_name="文章标题")
    # tec/no-tec
    category = models.CharField(max_length=20, verbose_name="文章分类")
    # public/private
    limit = models.CharField(max_length=20, verbose_name="文章权限")
    introduce = models.CharField(max_length=90, verbose_name="文章简介")
    content = models.TextField(verbose_name="文章内容")
    created_time = models.DateTimeField(auto_now_add=True)
    updated_time = models.DateTimeField(auto_now=True)
    author = models.ForeignKey(UserProfile, on_delete=models.CASCADE) # 要死一起死

