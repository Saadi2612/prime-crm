from rest_framework import viewsets, filters, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import PermissionDenied, ValidationError
from django.db.models import Count, Q, Prefetch
from django.utils import timezone
from datetime import timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from leads.models import Lead, LeadNote, LeadStage, LeadTransfer
from leads.serializers import LeadSerializer, LeadListSerializer, LeadDetailSerializer, LeadTransferSerializer
from authentication.models import User


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
        is_detailed=false → id, full_name, phone, job_title, project only
        is_paginated=true → paginated response (default)
        is_paginated=false → all objects in one response
    """
    queryset = Lead.objects.select_related(
        'project', 'stage', 'assigned_to'
    ).prefetch_related(
        Prefetch(
            'notes',
            queryset=LeadNote.objects.order_by('-created_at'),
            to_attr='prefetched_notes',
        )
    ).all()
    serializer_class = LeadSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['full_name', 'phone', 'job_title', 'form_id']
    ordering_fields = ['full_name', 'min_budget', 'max_budget', 'created_at']
    ordering = ['-created_at']

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        if self.action in ['list', 'stats', 'chart', 'recent', 'unassigned_leads'] and user.is_authenticated:
            if user.role == 'agent':
                return queryset.filter(assigned_to=user)
            # Admin/manager can filter by assigned_to query param
            assigned_to_id = self.request.query_params.get('assigned_to')
            if assigned_to_id:
                queryset = queryset.filter(assigned_to__id=assigned_to_id)
            # Admin/manager can filter for unassigned leads
            if self.request.query_params.get('unassigned') == 'true':
                queryset = queryset.filter(assigned_to__isnull=True)
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

    @action(detail=False, methods=['get'])
    def stats(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        today = timezone.localtime().date()

        # Single query: total, active, and qualified counts via conditional aggregation
        aggregates = queryset.aggregate(
            total_leads=Count('id'),
            active_leads=Count('id', filter=~Q(stage__name__in=['lost', 'qualified'])),
            qualified_leads=Count('id', filter=Q(stage__name='qualified')),
        )

        # Separate query for follow-ups (different table) — direct join, no subquery
        follow_ups_today = (
            LeadNote.objects
            .filter(next_follow_up__date=today, lead__in=queryset.values('id'))
            .values('lead_id')
            .distinct()
            .count()
        )

        stage_counts = {
            item['stage__name'].lower(): item['count']
            for item in queryset.values('stage__name').annotate(count=Count('id'))
            if item['stage__name']
        }

        return Response({
            **aggregates,
            'follow_ups_today': follow_ups_today,
            'stage_counts': stage_counts,
        })

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='days',
                type=OpenApiTypes.INT,
                location=OpenApiParameter.QUERY,
                required=False,
                default=7,
                description='Number of days for chart data (7 or 30).',
            ),
        ],
    )
    @action(detail=False, methods=['get'])
    def chart(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        try:
            days = int(request.query_params.get('days', 7))
            if days not in [7, 30]:
                days = 7
        except ValueError:
            days = 7
            
        today = timezone.localtime().date()
        threshold_date = today - timedelta(days=days - 1)

        print("threshold -> ", threshold_date, flush=True)
        
        # Filter leads created from threshold date to today
        # Note: created_time might be a datetime, so we filter by date
        filtered_leads = queryset.filter(
            created_time__date__gte=threshold_date,
            created_time__date__lte=today
        )
        
        # Group by date and count
        leads_per_day = filtered_leads.values('created_time__date').annotate(count=Count('id')).order_by('created_time__date')
        
        # Format the result to ensure all dates exist even if 0 count
        result_dict = {
            (threshold_date + timedelta(days=i)).strftime('%Y-%m-%d'): 0
            for i in range(days)
        }
        
        for item in leads_per_day:
            date_str = item['created_time__date'].strftime('%Y-%m-%d')
            result_dict[date_str] = item['count']
            
        formatted_result = [{'date': date, 'count': count} for date, count in result_dict.items()]
        
        return Response(formatted_result)

    @action(detail=False, methods=['get'])
    def recent(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        
        today = timezone.localtime().date()
        recent_leads = queryset.filter(created_time__date=today).order_by('-created_time')[:10]
        
        serializer = LeadListSerializer(recent_leads, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='unassigned')
    def unassigned_leads(self, request):
        """GET /leads/unassigned/
        Returns all leads with no assigned user.
        Only accessible by admin and manager roles.
        """
        user = request.user
        if getattr(user, 'role', '') not in ('admin', 'manager'):
            raise PermissionDenied("Only admins and managers can view unassigned leads.")

        queryset = self.filter_queryset(
            Lead.objects.select_related('project', 'stage', 'assigned_to')
            .filter(assigned_to__isnull=True)
            .order_by('-created_at')
        )
        serializer = LeadSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='today-follow-ups')
    def today_follow_ups(self, request):
        """Get today's follow-ups for the user."""
        from leads.serializers.lead_note import FollowUpSerializer

        user = request.user
        today = timezone.localtime().date()

        # Build note filter directly — avoids passing a full queryset as a correlated subquery
        notes_qs = LeadNote.objects.select_related('lead').filter(
            next_follow_up__date=today
        )
        if getattr(user, 'role', '') == 'agent':
            # Direct join on assigned_to — fastest path for agents
            notes_qs = notes_qs.filter(lead__assigned_to=user)
        else:
            # Admin/manager: optionally filter by assigned_to query param
            assigned_to_id = request.query_params.get('assigned_to')
            if assigned_to_id:
                notes_qs = notes_qs.filter(lead__assigned_to__id=assigned_to_id)

        serializer = FollowUpSerializer(notes_qs.order_by('next_follow_up'), many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'], url_path='transfer')
    def transfer(self, request, pk=None):
        """
        POST /leads/{id}/transfer/
        Body: { "to_user": "<uuid>", "note": "optional" }

        Reassigns the lead to a different agent and records the transfer.
        Only admin and manager roles are allowed.
        """
        user = request.user
        if getattr(user, 'role', '') not in ('admin', 'manager'):
            raise PermissionDenied("Only admins and managers can transfer leads.")

        lead = self.get_object()

        to_user_id = request.data.get('to_user')
        if not to_user_id:
            raise ValidationError({'to_user': 'This field is required.'})

        try:
            to_user = User.objects.get(pk=to_user_id)
        except User.DoesNotExist:
            raise ValidationError({'to_user': 'User not found.'})

        note = request.data.get('note', '')

        LeadTransfer.objects.create(
            lead=lead,
            from_user=lead.assigned_to,
            to_user=to_user,
            transferred_by=user,
            note=note,
        )

        lead.assigned_to = to_user
        lead.save(update_fields=['assigned_to'])

        serializer = LeadDetailSerializer(lead, context={'request': request})
        return Response(serializer.data, status=status.HTTP_200_OK)

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name='is_detailed',
                type=OpenApiTypes.BOOL,
                location=OpenApiParameter.QUERY,
                required=False,
                default=True,
                description='Return full lead details (true) or slim fields only — id, full_name, phone, job_title, project (false).',
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

    def perform_create(self, serializer):
        stage = LeadStage.objects.filter(name__iexact='new').first()
        if not stage:
            stage, _ = LeadStage.objects.get_or_create(name='new', defaults={'order': 0})
        serializer.save(assigned_to=self.request.user, stage=stage)

    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        return super().update(request, *args, **kwargs)

    def partial_update(self, request, *args, **kwargs):
        return super().partial_update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        return super().destroy(request, *args, **kwargs)
