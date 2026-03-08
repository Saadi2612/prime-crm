from rest_framework import viewsets, filters
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from projects.models import Project
from projects.serializers import ProjectSerializer, ProjectListSerializer


class ProjectViewSet(viewsets.ModelViewSet):
    """
    ViewSet for performing CRUD operations on Projects.

    list:           GET  /projects/
    create:         POST /projects/
    retrieve:       GET  /projects/{id}/
    update:         PUT  /projects/{id}/
    partial_update: PATCH /projects/{id}/
    destroy:        DELETE /projects/{id}/

    Query Params (list only):
        is_detailed=true  → full object (default behaviour)
        is_detailed=false → id, name, type, size, size_unit only
        is_paginated=true → paginated response (default behaviour)
        is_paginated=false → all objects in one response
    """
    queryset = Project.objects.all()
    serializer_class = ProjectSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'form_id']
    ordering_fields = ['name', 'size', 'created_at']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'list':
            is_detailed = self.request.query_params.get('is_detailed', 'true').lower()
            if is_detailed != 'true':
                return ProjectListSerializer
        return ProjectSerializer

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
                description='Return full project details (true) or slim fields only — id, name, type, size, size_unit (false).',
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
