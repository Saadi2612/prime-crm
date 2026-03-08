from rest_framework import viewsets, filters
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from leads.models import Lead
from leads.serializers import LeadSerializer, LeadListSerializer, LeadDetailSerializer


class LeadViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on Leads.

    list:           GET  /leads/
    create:         POST /leads/
    retrieve:       GET  /leads/{id}/
    update:         PUT  /leads/{id}/
    partial_update: PATCH /leads/{id}/
    destroy:        DELETE /leads/{id}/

    Query Params (list only):
        is_detailed=true  → full object (default)
        is_detailed=false → id, full_name, phone, job_title, next_follow_up, project only
        is_paginated=true → paginated response (default)
        is_paginated=false → all objects in one response
    """
    queryset = Lead.objects.select_related('project', 'stage', 'assigned_to').all()
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'phone', 'job_title', 'form_id']
    ordering_fields = ['full_name', 'next_follow_up', 'min_budget', 'max_budget', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if self.action == 'list' and user.is_authenticated:
            if getattr(user, 'role', '') == 'agent':
                return queryset.filter(assigned_to=user)
        return queryset

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        if user.is_authenticated:
            if getattr(user, 'role', '') == 'agent':
                if self.action == 'destroy':
                    raise PermissionDenied("Agents are not allowed to delete leads.")
                if obj.assigned_to != user:
                    raise PermissionDenied("You do not have permission to access this lead.")
        return obj

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return LeadDetailSerializer
        if self.action == 'list':
            is_detailed = self.request.query_params.get('is_detailed', 'true').lower()
            if is_detailed != 'true':
                return LeadListSerializer
        return LeadSerializer

    def get_paginated_response(self, data):
        is_paginated = self.request.query_params.get('is_paginated', 'true').lower()
        if is_paginated != 'true':
            return Response(data)
        return super().get_paginated_response(data)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='is_detailed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                default=True,
                description='Return full lead details (true) or slim fields only — id, full_name, phone, job_title, next_follow_up, project (false).',
            ),
            OpenApiParameter(
                name='is_paginated',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                default=True,
                description='Return a paginated response (true) or all results in a single list (false).',
            ),
        ],
    )
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
