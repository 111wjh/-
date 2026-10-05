"""应用配置。

Django 会在 INSTALLED_APPS 里写 "blog" 时自动找到这个类，
用它给应用起个中文名、设置默认主键类型等。
"""

from django.apps import AppConfig


class BlogConfig(AppConfig):
    name = "blog"
    # 后台里显示的应用名，改成中文后 Django Admin 的菜单更好认
    verbose_name = "博客"
