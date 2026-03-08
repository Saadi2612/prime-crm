import os
from .common import *

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-0#r^1yas045z^_j0e)o*x2q^%kmy(3t@j1g-a1yanm1-r)83(t')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', 'prime-crm-production-88.up.railway.app,localhost').split(',')

CSRF_TRUSTED_ORIGINS = [
    'https://prime-crm-production-88.up.railway.app',
    'https://prime-crm-fe.vercel.app'
]

CORS_ALLOWED_ORIGINS = [
    'https://prime-crm-production-88.up.railway.app',
    'https://prime-crm-fe.vercel.app'
]
CORS_ALLOW_CREDENTIALS = True
