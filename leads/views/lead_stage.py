from authentication.permissions import IsAdminOrManager
from rest_framework import viewsets, filters
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated

from leads.models import LeadStage
from leads.serializers import LeadStageSerializer

class LeadStageViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing Lead pipeline stages.

    list:           GET  /leads/stages/
    create:         POST /leads/stages/
    retrieve:       GET  /leads/stages/{id}/
    update:         PUT  /leads/stages/{id}/
    partial_update: PATCH /leads/stages/{id}/
    destroy:        DELETE /leads/stages/{id}/

    Default stages (New, Contacted, Negotiation, Won, Lost) are seeded
    """
    queryset = LeadStage.objects.all()
    serializer_class = LeadStageSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name']
    ordering_fields = ['order', 'name', 'created_at']
    ordering = ['order', 'name']

    def get_permissions(self):
        if self.action == 'list':
            return [IsAuthenticated()]
        return [IsAdminOrManager()]

    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
