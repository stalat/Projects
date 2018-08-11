"""
Django settings for WebTek project.

For more information on this file, see
https://docs.djangoproject.com/en/1.7/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/1.7/ref/settings/
"""

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
import os
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
print "@@@@@@@@@@@@@@@@@@@@@", BASE_DIR

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/1.7/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'e%y5k4#afx#3f1%w9d$2#lmol*fb5xb@arbc3v%*g_hhc09u#u'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

TEMPLATE_DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = (
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'student'
)

MIDDLEWARE_CLASSES = (
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.auth.middleware.SessionAuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
)

ROOT_URLCONF = 'WebTek.urls'

WSGI_APPLICATION = 'WebTek.wsgi.application'


# Database
# https://docs.djangoproject.com/en/1.7/ref/settings/#databases

DATABASES = {
        'default': {
        'ENGINE': 'django.db.backends.mysql', 
        'NAME': 'webtek_004',
        'USER': 'root',
        'PASSWORD': 'UbUroot1',
        'HOST': 'localhost',   # Or an IP Address that your DB is hosted on
        'PORT': '3306',
                   }
}
# Internationalization
# https://docs.djangoproject.com/en/1.7/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/1.7/howto/static-files/

STATIC_URL = '/static/'
print ">>>>>>>>>>>>>>>>>>>>>>>>>>>>>", os.path.join(BASE_DIR, '/templates')

TEMPLATES = [
    {
                'BACKEND': 'django.template.backends.django.DjangoTemplates',
                        'DIRS': ["/home/talat/Talat/webtek_004/Second_Last/WebTek/templates"],
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

STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
        ]


