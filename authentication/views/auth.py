from drf_spectacular.utils import OpenApiExample, OpenApiResponse, extend_schema, inline_serializer
from rest_framework import serializers as drf_serializers
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from authentication.serializers.auth import (
    ChangePasswordSerializer,
    LoginSerializer,
    UserProfileSerializer,
)


class LoginView(APIView):
    """Authenticate with email + password and receive JWT tokens."""
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Login',
        description='Authenticate with email and password. Returns JWT access + refresh tokens and the user profile.',
        request=LoginSerializer,
        responses={
            200: OpenApiResponse(
                description='Login successful',
                response=inline_serializer(
                    name='LoginResponse',
                    fields={
                        'access': drf_serializers.CharField(),
                        'refresh': drf_serializers.CharField(),
                        'user': UserProfileSerializer(),
                    },
                ),
                examples=[
                    OpenApiExample(
                        'Success',
                        value={
                            'access': '<jwt-access-token>',
                            'refresh': '<jwt-refresh-token>',
                            'user': {
                                'id': 1,
                                'email': 'admin@example.com',
                                'role': 'admin',
                                'first_name': 'John',
                                'last_name': 'Doe',
                            },
                        },
                    )
                ],
            ),
            400: OpenApiResponse(description='Invalid credentials'),
        },
        auth=[],
        tags=['Authentication'],
    )
    def post(self, request):
        print("email:   ", request.data['email'])
        print("password:   ", request.data['password'])
        
        serializer = LoginSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserProfileSerializer(user).data,
        }, status=status.HTTP_200_OK)


class LogoutView(APIView):
    """Blacklist the refresh token to invalidate the current session."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Logout',
        description='Blacklist the provided refresh token, effectively logging out the user.',
        request=inline_serializer(
            name='LogoutRequest',
            fields={'refresh': drf_serializers.CharField(help_text='The JWT refresh token to blacklist.')},
        ),
        responses={
            200: OpenApiResponse(description='Logged out successfully'),
            400: OpenApiResponse(description='Missing or invalid refresh token'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response(
                {'detail': 'Refresh token is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            return Response(
                {'detail': 'Invalid or already blacklisted token.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response({'detail': 'Successfully logged out.'}, status=status.HTTP_200_OK)


class ChangePasswordView(APIView):
    """Change the authenticated user's password."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Change Password',
        description='Change your password. Requires the current (old) password for verification.',
        request=ChangePasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password changed successfully'),
            400: OpenApiResponse(description='Validation error — wrong old password or mismatched new passwords'),
        },
        tags=['Authentication'],
    )
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {'detail': 'Password changed successfully.'},
            status=status.HTTP_200_OK,
        )


class MeView(APIView):
    """Retrieve the profile of the currently authenticated user."""
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='My Profile',
        description='Returns the profile of the currently authenticated user.',
        responses={
            200: UserProfileSerializer,
            401: OpenApiResponse(description='Authentication credentials were not provided'),
        },
        tags=['Authentication'],
    )
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
