from django.db.models import Count, Q
from drf_spectacular.utils import OpenApiParameter, OpenApiResponse, extend_schema
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import User
from authentication.serializers.auth import UserProfileSerializer, UserUpdateSerializer

def _annotate_lead_stats(queryset):
    return queryset.annotate(
        total_leads_count=Count('assigned_leads', distinct=True),
        won_leads_count=Count('assigned_leads', filter=Q(assigned_leads__stage__name='Qualified'), distinct=True),
        lost_leads_count=Count('assigned_leads', filter=Q(assigned_leads__stage__name='Lost'), distinct=True),
        active_leads_count=Count('assigned_leads', filter=~Q(assigned_leads__stage__name__in=['New', 'Qualified', 'Lost']), distinct=True),
    )


class UserListView(APIView):
    """
    List all non-admin users (agents + managers).

    Optional query param:
        role=agent  → return only agents
        role=manager → return only managers
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='List Users',
        description=(
            'Returns a list of all active agents and managers. '
            'Filter by role using the `role` query parameter (`agent` or `manager`).'
        ),
        parameters=[
            OpenApiParameter(
                name='role',
                description='Filter by role. Accepted values: `agent`, `manager`.',
                required=False,
                type=str,
                enum=['agent', 'manager'],
            )
        ],
        responses={
            200: UserProfileSerializer(many=True),
            400: OpenApiResponse(description='Invalid role value'),
        },
        tags=['Users'],
    )
    def get(self, request):
        role = request.query_params.get('role')
        valid_roles = {User.Role.AGENT, User.Role.MANAGER}

        if role:
            if role not in valid_roles:
                return Response(
                    {'detail': f'Invalid role "{role}". Valid values: agent, manager.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            queryset = User.objects.filter(role=role, is_active=True)
        else:
            queryset = User.objects.filter(role__in=valid_roles, is_active=True)

        queryset = _annotate_lead_stats(queryset)

        serializer = UserProfileSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)


class UpdateMeView(APIView):
    """
    Allow the currently authenticated user to update their own profile.
    Only first_name, last_name, and phone_number are writable.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Update My Profile',
        description=(
            'Update your own profile information. '
            'Only `first_name`, `last_name`, and `phone_number` can be changed. '
            'Supports partial updates (PATCH).'
        ),
        request=UserUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: OpenApiResponse(description='Validation error'),
        },
        tags=['Users'],
    )
    def patch(self, request):
        serializer = UserUpdateSerializer(
            request.user,
            data=request.data,
            partial=True,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        user_with_stats = _annotate_lead_stats(User.objects.filter(id=request.user.id)).first()
        if user_with_stats:
            request.user = user_with_stats
            
        return Response(
            UserProfileSerializer(request.user).data,
            status=status.HTTP_200_OK,
        )


class UserDetailView(APIView):
    """
    Retrieve a single user's profile by ID.
    Only active agents and managers can be retrieved.
    """
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get User Detail',
        description='Retrieve a specific team member by their UUID.',
        responses={
            200: UserProfileSerializer,
            404: OpenApiResponse(description='User not found'),
        },
        tags=['Users'],
    )
    def get(self, request, pk):
        valid_roles = {User.Role.AGENT, User.Role.MANAGER}
        
        try:
            queryset = User.objects.filter(pk=pk, role__in=valid_roles, is_active=True)
            queryset = _annotate_lead_stats(queryset)
            user = queryset.get()
            serializer = UserProfileSerializer(user)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except User.DoesNotExist:
            return Response(
                {'detail': 'User not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
