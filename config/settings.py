"""
Django settings for config project.

Generated by 'django-admin startproject' using Django 4.0.2.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
from django.contrib.messages import constants as messages

from celery.schedules import crontab

from datetime import timedelta
from pathlib import Path
from environ import Env
import sys

env = Env()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DJAGNO_DEBUG')

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # third party
    'phonenumber_field',
    'rest_framework',
    'rest_framework_simplejwt',
    'crispy_forms',
    "crispy_bootstrap5",
    'django_otp',
    'drf_spectacular',
    'celery',
    'django_celery_beat',
    'axes',

    # app local
    'ads',
    'accounts',
    'payment',
]

MIDDLEWARE = [
    # Default middlewares
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # Middleware for enhanced security and protection against brute-force login attempts using Django Axes.
    'axes.middleware.AxesMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [str(BASE_DIR.joinpath('templates')), ],
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

WSGI_APPLICATION = 'config.wsgi.application'

# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'postgres',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': 5432
        # 'ENGINE': 'django.db.backends.sqlite3',
        # 'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = '/static/'
STATICFILES_DIRS = (str(BASE_DIR.joinpath('static')),)

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = str(BASE_DIR.joinpath('media'))

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# config rest django
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': (
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ),
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
}

# config rest django jwt
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(days=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=40),
}

# config spectacular
SPECTACULAR_SETTINGS = {
    'TITLE': 'Wall',
    'DESCRIPTION': 'See ads and create your ads',
    'VERSION': '1.0.0',
    'SERVE_INCLUDE_SCHEMA': False,
    'COMPONENT_SPLIT_REQUEST': True,
}

# CustomUser
AUTH_USER_MODEL = 'accounts.CustomUser'
LOGOUT_REDIRECT_URL = 'home'

MAX_LOGIN = 3
LOGIN_SUCCESS_CHECK_PERIOD_MINUTE = 20
BLOCK_TIME_MAX_LOGIN_MINUTE = 60

# Custom Authentication Backends Configuration
# -------------------------------------------
# Define the order of authentication backends for user login.
# 1. 'AxesStandaloneBackend': Handles rate limiting and blocking for login attempts.
# 2. 'UsernameOrPhoneModelBackend': Custom backend that allows login using either username or phone number.
#    - Uses username for admin panel login.
#    - Uses phone number for normal user login.
# 3. 'ModelBackend': Default Django authentication backend for username and password.
AUTHENTICATION_BACKENDS = [
    'axes.backends.AxesStandaloneBackend',  # Rate limiting and blocking
    'accounts.backends.UsernameOrPhoneModelBackend',  # Custom login with flexible username/phone
    'django.contrib.auth.backends.ModelBackend',  # Default username and password login
]

# config django axes
AXES_FAILURE_LIMIT = 5  # Maximum allowed login failures before lockout.
AXES_LOCK_OUT_AT_FAILURE = True  # Enable lockout after exceeding failure limit.
AXES_COOLOFF_TIME = 0.04   # Time period (in days) for cooling off during lockout.
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False  # Don't reset cool-off time on each failure during lockout.
AXES_PASSWORD_FORM_FIELD = 'code'  # Using 'code' as the password-equivalent field for rate limiting.
AXES_USERNAME_FORM_FIELD = 'phone_number'  # Name of the form field for the username or identifier.
AXES_LOCKOUT_CALLABLE = 'accounts.utils.custom_lockout_response'

# crispy form
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# config messages
MESSAGE_TAGS = {
    messages.ERROR: 'danger',
}

# config otp
MAX_OTP_TRY = 2
RESET_TIME_OTP_MINUTE = 4
LIMIT_TIME_MAX_OTP = 1

# config ads
FREE_ADS_MONTHLY_QUOTA = 3  # Limit create ads
MIN_REPORTS_TO_BLOCK_AD = 5  # Minimum reports to block an ad

# price ad token for one
AD_TOKEN_PRICE = env.int('AD_TOKEN_PRICE')

# Maximum Discount Percentage
# This variable represents the maximum allowable discount percentage
# that can be applied to an item's price. It defines the threshold
# below which a discount price is considered invalid. For example,
# if set to 30, it allows a calculated discount price to be up to
# 30% smaller than the original price.
MAX_DISCOUNT_PERCENT = 70

# config celery
CELERY_BROKER_URL = 'redis://redis:6379/0'
CELERY_RESULT_BACKEND = CELERY_BROKER_URL
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_DEFAULT_QUEUE = 'default'

CELERY_BEAT_SCHEDULE = {
    'remove_ads_expired': {
        'task': 'ads.tasks.check_expiration_date_every_day',
        'schedule': crontab(minute='0', hour='0'),
    },
    'block_ads': {
        'task': 'ads.tasks.check_reports_of_ads',
        'schedule': crontab(minute='0', hour='1'),
    },
}

# Setting to detect if the app is running tests
TESTING = len(sys.argv) > 1 and sys.argv[1] == 'test'
