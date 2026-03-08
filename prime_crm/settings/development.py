from .common import *

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-0#r^1yas045z^_j0e)o*x2q^%kmy(3t@j1g-a1yanm1-r)83(t'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = ['muskox-dynamic-mutually.ngrok-free.app', 'localhost', '127.0.0.1', 'prime-crm-fe.vercel.app', 'prime-crm-production-88.up.railway.app']

CSRF_TRUSTED_ORIGINS = [
    'http://localhost:3000', 
    'https://muskox-dynamic-mutually.ngrok-free.app',
    'https://prime-crm-fe.vercel.app',
    'https://prime-crm-production-88.up.railway.app'
]

CORS_ALLOW_ALL_ORIGINS = False
CORS_ALLOWED_ORIGINS = [
    'http://localhost:3000', 
    'https://muskox-dynamic-mutually.ngrok-free.app',
    'https://prime-crm-fe.vercel.app',
    'https://prime-crm-production-88.up.railway.app'
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_HEADERS = [
    "accept",
    "accept-encoding",
    "authorization",
    "content-type",
    "dnt",
    "origin",
    "user-agent",
    "x-csrftoken",
    "x-requested-with",
]
CORS_ALLOW_METHODS = [
    "DELETE",
    "GET",
    "OPTIONS",
    "PATCH",
    "POST",
    "PUT",
]

    
