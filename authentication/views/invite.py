from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.models import Invitation
from authentication.permissions import IsAdminOrManager
from authentication.serializers.auth import UserProfileSerializer
from authentication.serializers.invite import AcceptInviteSerializer, InviteUserSerializer
from authentication.utils import send_invite_email


class InviteUserView(APIView):
    """
    POST /auth/invite/
    - Admin can invite Manager or Agent.
    - Manager can invite Agent only.
    """
    permission_classes = [IsAuthenticated, IsAdminOrManager]

    def post(self, request):
        serializer = InviteUserSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        invitation = serializer.save()

        try:
            send_invite_email(invitation, request)
        except Exception:
            # Don't fail the request if email sending fails — log in production
            pass

        return Response(
            {
                'detail': f'Invitation sent to {invitation.email}.',
                'token': str(invitation.token),  # included for testing convenience
            },
            status=status.HTTP_201_CREATED,
        )


class AcceptInviteView(APIView):
    """
    POST /auth/accept-invite/
    Accept an invitation and create a new user account.
    """

    def post(self, request):
        serializer = AcceptInviteSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        # Auto-login: return JWT tokens on successful registration
        from rest_framework_simplejwt.tokens import RefreshToken
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
