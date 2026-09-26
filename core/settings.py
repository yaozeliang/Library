"""Django settings for Library Management System.

Copyright (c) 2019 - present AppSeed.us
"""

import os

from decouple import config

from core.db_config import databases_from_url
from core.production_config import LOCAL_DEV_SECRET_KEY

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Local installs may omit SECRET_KEY. Production settings refuse this placeholder.
SECRET_KEY = config("SECRET_KEY", default=LOCAL_DEV_SECRET_KEY)

# SECURITY WARNING: don't run with debug turned on in production!
# Local default stays on. Production settings default this off.
DEBUG = config("DEBUG", default=True, cast=bool)
# load production server from .env
ALLOWED_HOSTS = ["localhost", "127.0.0.1", config("SERVER", default="127.0.0.1")]

# Application definition

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "book",
    "crispy_forms",
    "crispy_bootstrap4",
    "crispy_tailwind",
    "phonenumber_field",
    "bootstrap4",
    "bootstrap_datepicker_plus",
    "rest_framework",
    "ckeditor",
    "comment",
    "notifications",
    "django_flatpickr",
    "storages",
]

CRISPY_ALLOWED_TEMPLATE_PACKS = ("bootstrap4", "tailwind")
CRISPY_TEMPLATE_PACK = "bootstrap4"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    # 'django.middleware.cache.UpdateCacheMiddleware', # Redis
    "django.middleware.common.CommonMiddleware",
    # 'django.middleware.cache.FetchFromCacheMiddleware',     # Redis
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

CKEDITOR_CONFIGS = {
    # django-ckeditor默认使用default配置
    "default": {
        # 编辑器宽度自适应
        "width": "auto",
        "height": "150px",
        # tab键转换空格数
        "tabSpaces": 4,
        # 工具栏风格
        "toolbar": "Custom",
        # 工具栏按钮
        "toolbar_Custom": [
            # 表情 代码块
            ["Smiley", "CodeSnippet"],
            # 字体风格
            ["Bold", "Italic", "Underline", "RemoveFormat", "Blockquote"],
            # 字体颜色
            ["TextColor", "BGColor"],
            # 链接
            ["Link", "Unlink"],
            # 列表
            ["NumberedList", "BulletedList"],
            # 最大化
            ["Maximize"],
        ],
        # 加入代码块插件
        "extraPlugins": ",".join(["codesnippet"]),
    },
}

REST_FRAMEWORK = {
    # Every DRF view (the routes under /api/) requires an authenticated
    # superuser or a member of the api group. Superusers pass without the
    # group. A view-level permission_classes list replaces this default;
    # leaving IsAuthenticated on a view drops the group check.
    "DEFAULT_PERMISSION_CLASSES": [
        "Api.permissions.IsSuperuserOrApiGroup",
    ],
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 10,
}

ROOT_URLCONF = "core.urls"
LOGIN_REDIRECT_URL = "home"
LOGOUT_REDIRECT_URL = "home"
TEMPLATE_DIR = os.path.join(BASE_DIR, "templates")  # ROOT dir for templates

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [TEMPLATE_DIR],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                # 'django.contrib.messages.context_processors.media',
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "core.wsgi.application"

# Postgres when DATABASE_URL is set (for example DigitalOcean Managed Postgres,
# database defaultdb, schema library). SQLite when it is unset.
DATABASES = databases_from_url(config("DATABASE_URL", default=""))

# Password validation
# https://docs.djangoproject.com/en/3.0/ref/settings/#auth-password-validators

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

ELASTICSEARCH_DSL = {
    "default": {
        "hosts": "localhost:9200",
    },
}

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"
TIME_ZONE = "Europe/Paris"

USE_I18N = True

USE_TZ = True

LOGGING_DIR = os.path.join(BASE_DIR, "logging")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s %(name)-12s %(lineno)d %(levelname)-8s %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
        },
        "mail_admins": {
            "level": "ERROR",
            "class": "django.utils.log.AdminEmailHandler",
        },
        "file": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": os.path.join(LOGGING_DIR, "book.admin.log"),
        },
        "performance": {
            "level": "INFO",
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": os.path.join(LOGGING_DIR, "performance.log"),
        },
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
        "django.request": {
            "handlers": ["mail_admins"],
            "level": "ERROR",
            "propagate": False,
        },
        "book": {
            "handlers": ["console", "file"],
            "level": "INFO",
            "propagate": True,
        },
    },
}

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.0/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = os.path.join(BASE_DIR, "staticfiles")
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, "static"),
]

# Media files
MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, "media")

# Existing tables use integer primary keys created under Django 2.2.
# BigAutoField would rewrite every id column on migrate.
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"
