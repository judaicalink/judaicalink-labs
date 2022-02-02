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

# Raises Django's ImproperlyConfigured
# exception if SECRET_KEY not in os.environ
# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('SECRET_KEY')

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/2.2/howto/deployment/checklist/

ALLOWED_HOSTS = [
    'labs.judaicalink.org',
    'localhost'
]

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
    'captcha',
    'hcaptcha',
    'active_link',
    'environ',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
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

CACHES = {
    # Read os.environ['CACHE_URL'] and raises
    # ImproperlyConfigured exception if not found.
    #
    # The cache() method is an alias for cache_url().
    'default': env.cache(),

    # read os.environ['REDIS_URL']
    'redis': env.cache_url('REDIS_URL')
}

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
STATIC_ROOT = os.path.join(BASE_DIR, "static/")

# Crispy form
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

# labs settings
LABS_ROOT = env('LABS_ROOT') if env('LABS_ROOT') is not None else 'http://localhost:8000'
LABS_GIT_WEBROOT = env('LABS_GIT_WEBROOT') if env('LABS_GIT_WEBROOT') is not None else "https://github.com/wisslab/judaicalink-labs/blob/master/labs/"
LABS_DUMPS_WEBROOT = env('LABS_DUMPS_WEBROOT') if env('LABS_DUMPS_WEBROOT') is not None else "http://data.judaicalink.org/dumps/"
LABS_DUMPS_LOCAL = env('LABS_DUMPS_LOCAL') if env('LABS_DUMPS_LOCAL') is not None else "dumps/"

# Fuseki
FUSEKI_SERVER = env('FUSEKI_SERVER') if env('FUSEKI_SERVER') is not None else "http://localhost:3030"
FUSEKI_STORAGE = env('FUSEKI_STORAGE') if env('FUSEKI_STORAGE') is not None else "."


# Elasticsearch
ELASTICSEARCH_SERVER = "https://localhost:9200/" if env('ELASTICSEARCH_SERVER') is None else env('ELASTICSEARCH_SERVER')
ELASTICSEARCH_STORAGE = "/var/lib/elasticsearch"
ELASTICSEARCH_SSL_ENABLED = False if ELASTICSEARCH_SERVER.startswith("http://") else True
JUDAICALINK_INDEX = env('JUDAICALINK_INDEX') if env('JUDAICALINK_INDEX') is not None else "judaicalink"
COMPACT_MEMORY_INDEX = env('COMPACT_MEMORY_INDEX') if env('COMPACT_MEMORY_INDEX') is not None else "cm"
COMPACT_MEMORY_META_INDEX = env('COMPACT_MEMORY_META_INDEX') if env('COMPACT_MEMORY_META_INDEX') is not None else "cm_meta"

# HCaptcha
HCAPTCHA_SITEKEY = env('HCAPTCHA_SITEKEY')
HCAPTCHA_SECRET = env('HCAPTCHA_SECRET')

HCAPTCHA_DEFAULT_CONFIG = {
    'onload': 'name_of_js_function',
    'render': 'explicit',
    'theme': 'light',  # do not use data- prefix
    'size': 'normal',  # do not use data- prefix
}


# if the settings in the .env contain the ELASTICSEARCH_SERVER_CERT_PATH use it, else throw an error
if ELASTICSEARCH_SSL_ENABLED and env('ELASTICSEARCH_SERVER_CERT_PATH') is not None:
    ELASTICSEARCH_SERVER_CERT_PATH = os.environ['ELASTICSEARCH_SERVER_CERT_PATH']
else:
    logging.ERROR("ELASTICSEARCH_SERVER_CERT_PATH not set in .env file")
    raise Exception('ELASTICSEARCH_SERVER_CERT_PATH not set in .env')

# Geonames
GEONAMES_API_USER = ""  # Configure in localsettings.py

if os.path.isfile("labs/localsettings.py"):
    from .localsettings import *
