from drf_spectacular.utils import OpenApiResponse, extend_schema, inline_serializer
from rest_framework import generics, serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import Invitation
from authentication.permissions import IsAdminOrManager
from authentication.serializers.auth import UserProfileSerializer
from authentication.serializers.invite import (
    AcceptInviteSerializer,
    InviteUserSerializer,
    PendingInvitationSerializer,
)
from authentication.utils import generate_invite_jwt, send_invite_email, send_welcome_email


class InviteUserView(APIView):
    """Send an invitation email to a new user."""
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @extend_schema(
        summary='Invite User',
        description=(
            'Send an invitation email with a unique sign-up link.\n\n'
            '**Role rules:**\n'
            '- Admin → can invite `manager` or `agent`\n'
            '- Manager → can invite `agent` only\n'
            '- Agent → not allowed'
        ),
        request=InviteUserSerializer,
        responses={
            201: OpenApiResponse(
                description='Invitation sent',
                response=inline_serializer(
                    name='InviteUserResponse',
                    fields={
                        'detail': drf_serializers.CharField(),
                        'token': drf_serializers.UUIDField(help_text='Invite token (for testing convenience)'),
                    },
                ),
            ),
            400: OpenApiResponse(description='Validation error — email already exists or invalid role'),
            403: OpenApiResponse(description='Permission denied — insufficient role'),
        },
        tags=['Invitations'],
    )
    def post(self, request):
        serializer = InviteUserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()

        invited_by = request.user

        jwt_token = generate_invite_jwt(invitation, invited_by)

        invitation.token = jwt_token
        invitation.save()

        try:
            send_invite_email(invitation, request)
        except Exception as e:
            # Don't fail the invite creation, but surface the error in logs
            import logging
            logging.getLogger(__name__).error('Failed to send invite email: %s', e)

        return Response(
            {
                'detail': f'Invitation sent to {invitation.email}.',
                'token': jwt_token,  # JWT token (for testing convenience)
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptInviteView(APIView):
    """Accept an invitation and create a new user account."""
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Accept Invite',
        description=(
            'Accept an invitation using the UUID token from the invite email. '
            'Creates a new user account and returns JWT tokens on success.'
        ),
        request=AcceptInviteSerializer,
        responses={
            201: OpenApiResponse(
                description='Account created — returns JWT tokens and user profile',
                response=inline_serializer(
                    name='AcceptInviteResponse',
                    fields={
                        'detail': drf_serializers.CharField(),
                        'access': drf_serializers.CharField(),
                        'refresh': drf_serializers.CharField(),
                        'user': UserProfileSerializer(),
                    },
                ),
            ),
            400: OpenApiResponse(description='Invalid, expired, or already-used token'),
        },
        auth=[],
        tags=['Invitations'],
    )
    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        try:
            send_welcome_email(user)
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Failed to send welcome email: %s', e)

        refresh = RefreshToken.for_user(user)

        return Response(
            {
                'detail': 'Account created successfully.',
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserProfileSerializer(user).data,
            },
            status=status.HTTP_201_CREATED,
        )


class PendingInvitationListView(generics.ListAPIView):
    """List all pending invitations."""
    serializer_class = PendingInvitationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    
    @extend_schema(summary='List Pending Invitations', tags=['Invitations'])
    def get_queryset(self):
        return Invitation.objects.filter(is_used=False)


class PendingInvitationDetailView(generics.DestroyAPIView):
    """Delete a pending invitation."""
    queryset = Invitation.objects.all()
    serializer_class = PendingInvitationSerializer
    permission_classes = [IsAuthenticated, IsAdminOrManager]
    
    @extend_schema(summary='Delete Pending Invitation', tags=['Invitations'])
    def delete(self, request, *args, **kwargs):
        # We can also add an extra verify if it is used, or let it delete anyway
        return super().delete(request, *args, **kwargs)


class ResendInvitationView(APIView):
    """Resend a pending invitation."""
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    @extend_schema(
        summary='Resend Invitation',
        description='Generates a new token for an existing invitation and resends the email.',
        responses={
            200: OpenApiResponse(description='Invitation resent successfully'),
            404: OpenApiResponse(description='Invitation not found or already used'),
        },
        tags=['Invitations'],
    )
    def post(self, request, pk):
        try:
            invitation = Invitation.objects.get(id=pk, is_used=False)
        except Invitation.DoesNotExist:
            return Response(
                {'detail': 'Active invitation not found.'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Generate new token
        invited_by = request.user
        jwt_token = generate_invite_jwt(invitation, invited_by)
        invitation.token = jwt_token
        # Refresh the expiration time using default_expires_at behavior
        from authentication.models.invite import default_expires_at
        invitation.expires_at = default_expires_at()
        invitation.save()

        try:
            # We construct a mock request to pass to send_invite_email to build absolute URI
            class MockRequest:
                def build_absolute_uri(self, location):
                    return request.build_absolute_uri(location)
            
            send_invite_email(invitation, MockRequest())
        except Exception as e:
            import logging
            logging.getLogger(__name__).error('Failed to resend invite email: %s', e)

        return Response(
            {'detail': f'Invitation resent to {invitation.email}.'},
            status=status.HTTP_200_OK
        )
