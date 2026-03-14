from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers as nested_routers

from .views import MetaWebhookView, LeadViewSet, LeadStageViewSet, LeadNoteViewSet, LeadTransferViewSet

app_name = 'leads'

# Top-level router
router = DefaultRouter()
router.register(r'stages', LeadStageViewSet, basename='lead-stage')
router.register(r'transfers', LeadTransferViewSet, basename='lead-transfer')
router.register(r'', LeadViewSet, basename='lead')

# Nested router: /leads/{lead_pk}/notes/
leads_router = nested_routers.NestedDefaultRouter(router, r'', lookup='lead')
leads_router.register(r'notes', LeadNoteViewSet, basename='lead-notes')
# Nested router: /leads/{lead_pk}/transfers/
leads_router.register(r'transfers', LeadTransferViewSet, basename='lead-transfers')

urlpatterns = [
    path('webhook/meta/', MetaWebhookView.as_view(), name='meta-webhook'),
    path('', include(router.urls)),
    path('', include(leads_router.urls)),
]
