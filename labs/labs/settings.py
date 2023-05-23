"""
Django settings for labs project.

Generated by 'django-admin startproject' using Django 2.2.6.

For more information on this file, see
https://docs.djangoproject.com/en/2.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/2.2/ref/settings/
"""
import logging

import environ
import os
from django.utils.translation import ugettext_lazy as _

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# SECURITY WARNING: don't run with debug turned on in production!
env = environ.Env(
    # set casting, default value
    DEBUG=(bool, False)
)

# Take environment variables from .env file
environ.Env.read_env(os.path.join(BASE_DIR, '.env'))

# False if not in os.environ because of casting above
DEBUG = env('DEBUG')
MODE = env('MODE')

# if MODE = preduction, then DEBUG = False
if env('MODE') == 'production':
    DEBUG = False

INTERNAL_IPS = env('INTERNAL_IPS').replace(" ", "").split(",")

# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

ALLOWED_HOSTS = env('ALLOWED_HOSTS').replace(" ", "").split(",")

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'channels',
    'core',
    'backend.apps.BackendConfig',
    'search',
    'cm_search',
    'cm_e_search',
    'lodjango',
    'dashboard',
    'data',
    'crispy_forms',
    'hcaptcha',
    'active_link',
    'environ',
    'debug_toolbar',
    'cookiebanner',
    'django.contrib.sitemaps',
    'django_extensions',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.gzip.GZipMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',
]

ROOT_URLCONF = 'labs.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
             os.path.join(BASE_DIR, 'templates'),
            ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
            'libraries': {
                'active_link_tags': 'active_link.templatetags.active_link_tags',
                'cookiebanner': 'cookiebanner.templatetags.cookiebanner',
            }
        },
    },
]

WSGI_APPLICATION = 'labs.wsgi.application'


# Database
# https://docs.djangoproject.com/en/2.2/ref/settings/#databases

DATABASES = {
    # read os.environ['DATABASE_URL'] and raises
    # ImproperlyConfigured exception if not found
    #
    # The db() method is an alias for db_url().
    'default': env.db(),

    # read os.environ['SQLITE_URL']
    'extra': env.db_url(
        'SQLITE_URL',
        default='sqlite:///db.sqlite3'
    )
}

# Cache
if 'CACHE_URL' in os.environ:
    CACHES = {
        'default': env.cache_url('CACHE_URL')
    }
elif 'REDIS_URL' in os.environ:
    CACHES = {
        'redis': env.cache_url('REDIS_URL')
    }
else:
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.dummy.DummyCache',
        }
    }


CACHE_TTL = 60 * 15

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Europe/Berlin'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, env('STATIC_ROOT') if env('STATIC_ROOT') else 'static')

#Crispy form
CRISPY_TEMPLATE_PACK = 'bootstrap4'

# Email settings
EMAIL_BACKEND = env('EMAIL_BACKEND')
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
EMAIL_TO = env('EMAIL_TO')

# Channels
ASGI_APPLICATION = "labs.routing.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer",
    },
}

# Other Servers
LABS_ROOT = env('LABS_ROOT')
FUSEKI_SERVER = env('FUSEKI_SERVER')
FUSEKI_STORAGE = env('FUSEKI_STORAGE')


# Elasticsearch
ELASTICSEARCH_SERVER = env('ELASTICSEARCH_SERVER') or "https://localhost:9200/"
ELASTICSEARCH_STORAGE = "/var/lib/elasticsearch"
ELASTICSEARCH_SSL_ENABLED = False if ELASTICSEARCH_SERVER.startswith("http://") else True
ELASTICSEARCH_USER = env('ELASTICSEARCH_USER') or "elastic"
ELASTICSEARCH_PASSWORD = env('ELASTICSEARCH_PASSWORD')
ELASTICSEARCH_SERVER_CERT = env('ELASTICSEARCH_SERVER_CERT') or None

JUDAICALINK_INDEX = env('JUDAICALINK_INDEX') or "judaicalink"
COMPACT_MEMORY_INDEX = env('COMPACT_MEMORY_INDEX') or "cm"
COMPACT_MEMORY_META_INDEX = env('COMPACT_MEMORY_META_INDEX') or "cm_meta"

# HCaptcha
HCAPTCHA_SITEKEY = env('HCAPTCHA_SITEKEY')
HCAPTCHA_SECRET = env('HCAPTCHA_SECRET')

HCAPTCHA_DEFAULT_CONFIG = {
    'onload': 'name_of_js_function',
    'render': 'explicit',
    'theme': 'light',  # do not use data- prefix
    'size': 'normal',  # do not use data- prefix
}

GEONAMES_API_USER = "" # Configure in localsettings.py

# removed
#if os.path.isfile("labs/localsettings.py"):
#    from .localsettings import *


# COOKIE_BANNER
COOKIEBANNER = {
    "title": _("Cookie settings"),
    "header_text": _("We are using cookies on this website. A few are essential, others are not."),
    "footer_text": _("Please accept our cookies"),
    "footer_links": [
        {"title": _("Imprint"), "href": "https://web.judaicalink.org/legal/"},
        {"title": _("Privacy"), "href": "https://web.judaicalink.org/legal/"},
    ],
    "groups": [
        {
            "id": "essential",
            "name": _("Essential"),
            "description": _("Essential cookies allow this page to work."),
            "cookies": [
                {
                    "pattern": "cookiebanner",
                    "description": _("Meta cookie for the cookies that are set."),
                },
                {
                    "pattern": "csrftoken",
                    "description": _("This cookie prevents Cross-Site-Request-Forgery attacks."),
                },
                {
                    "pattern": "sessionid",
                    "description": _("This cookie is necessary to allow logging in, for example."),
                },
            ],
        },
        {
            "id": "analytics",
            "name": _("Analytics"),
            "optional": False,
            "cookies": [
                {
                    "pattern": "_pk_.*",
                    "description": _("Matomo cookie for website analysis."),
                },
            ],
        },
    ],
}