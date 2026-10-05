"""项目总路由。

前后端分离后，后端只负责两类地址：
  1. /admin/  —— Django Admin，用来写文章、管理评论
  2. /api/    —— 给 Vue 前端调用的 JSON 接口（定义在 blog/urls.py 里）
"""

from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("blog.urls")),
]

# 开发环境下由 Django 直接把上传的图片发给浏览器；
# 生产环境应该交给 Nginx 之类的静态资源服务器
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
