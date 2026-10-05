"""blog 应用的路由表。

DefaultRouter 会根据 ViewSet 里的方法自动生成一批 URL，
所以这里只需要注册，不用一个个写 path()。
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from . import views

router = DefaultRouter()
# register(前缀, ViewSet, basename)：
# basename 用来给自动生成的路由起名，反查 URL 时要用到
router.register("posts", views.PostViewSet, basename="post")
router.register("categories", views.CategoryViewSet, basename="category")
router.register("tags", views.TagViewSet, basename="tag")
router.register("comments", views.CommentViewSet, basename="comment")

urlpatterns = [
    # 访问 /api/ 就会看到 DRF 自动生成的接口目录页
    path("", include(router.urls)),
    # 认证相关
    path("auth/register/", views.RegisterView.as_view(), name="auth_register"),
    path("auth/login/", views.LoginView.as_view(), name="auth_login"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="auth_refresh"),
    path("auth/me/", views.MeView.as_view(), name="auth_me"),
    # DRF 网页版接口的登录 / 登出，方便在浏览器里点着调试
    path("auth/", include("rest_framework.urls")),
    # 归档
    path("archive/", views.ArchiveView.as_view(), name="archive"),
]
