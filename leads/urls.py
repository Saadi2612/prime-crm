from django.urls import path

from .views import MetaWebhookView

app_name = 'leads'

urlpatterns = [
    path('webhook/meta/', MetaWebhookView.as_view(), name='meta-webhook'),
]
