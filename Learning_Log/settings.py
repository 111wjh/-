"""
Django settings for Learning_Log project.

学习要点：这个文件是「后端」的总开关 ——
用哪些插件、连哪个数据库、允许谁跨域访问接口、接口返回什么格式，都在这里决定。
"""

from datetime import timedelta
from pathlib import Path

# 项目根目录（manage.py 所在目录），下面很多路径都基于它拼接
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: 生产环境请把密钥放进环境变量，不要提交到 Git
SECRET_KEY = "django-insecure-nlo2m(nhlz&arixpas#qx*f@=@y9_rfshjfjxg3xv1nvn9_a=)"

# 开发阶段保持 True：报错页面会显示完整堆栈，方便学习调试
DEBUG = True

ALLOWED_HOSTS = ["127.0.0.1", "localhost"]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # 第三方插件
    "rest_framework",  # DRF：把 Python 对象变成 JSON 接口
    "corsheaders",  # 允许 Vue 前端（另一个端口）跨域调接口
    # 自己的应用
    "blog",
]

MIDDLEWARE = [
    # 跨域中间件要尽量靠前，最好放在 CommonMiddleware 之前
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "Learning_Log.urls"

# 前后端分离后，模板只服务于 Django Admin（写作后台）
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "Learning_Log.wsgi.application"
ASGI_APPLICATION = "Learning_Log.asgi.application"


# 学习阶段用 SQLite：零配置，一个文件就是整个数据库。
# 换成 PostgreSQL/MySQL 时只改这一块，业务代码一行都不用动
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",  # 用哪个数据库驱动
        "NAME": BASE_DIR / "db.sqlite3",  # 数据文件放在项目根目录
    }
}


# 密码强度规则。注册接口里的 validate_password() 用的就是这份配置
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# ------------------------- DRF（接口层）配置 -------------------------
REST_FRAMEWORK = {
    # 前端用 "Authorization: Bearer <access_token>" 调接口；
    # 保留 Session 是为了让 DRF 自带的网页版接口（Browsable API）能登录调试
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ),
    # 默认规则：所有人都能读，只有登录用户能写。个别视图再单独收紧或放宽
    "DEFAULT_PERMISSION_CLASSES": ("rest_framework.permissions.IsAuthenticatedOrReadOnly",),
    "DEFAULT_PAGINATION_CLASS": "blog.pagination.StandardPagination",
    "PAGE_SIZE": 8,
    "DATETIME_FORMAT": "iso-8601",
    "DEFAULT_THROTTLE_CLASSES": (
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ),
    "DEFAULT_THROTTLE_RATES": {
        "anon": "120/min",
        "user": "600/min",
    },
}

# JWT：一段带签名的字符串，服务端不用存 session 也能识别用户
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=60),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ------------------------- 跨域（CORS）配置 -------------------------
# 只有列表里的前端地址才允许调用本接口
CORS_ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:4173",
    "http://127.0.0.1:4173",
]
CORS_ALLOW_CREDENTIALS = True


# ------------------------- 国际化 -------------------------
LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True


# ------------------------- 静态文件与媒体文件 -------------------------
STATIC_URL = "static/"
# collectstatic 命令会把 Admin 的 CSS/JS 收集到这里，方便生产环境交给 Nginx
STATIC_ROOT = BASE_DIR / "staticfiles"

# 用户上传的图片（文章封面）保存目录
MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# Email：开发时邮件直接打印在终端里，不真的发出去
MAILERS = {
    "default": {
        "BACKEND": "django.core.mail.backends.console.EmailBackend",
    },
}
