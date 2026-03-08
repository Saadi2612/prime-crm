from drf_spectacular.utils import OpenApiResponse, extend_schema
from rest_framework.permissions import AllowAny
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from authentication.models import OTPCode
from authentication.serializers.password_reset import (
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    VerifyOTPSerializer,
)
from authentication.utils import generate_otp, send_otp_email


class ForgotPasswordView(APIView):
    """Request a one-time password (OTP) for password reset."""
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Forgot Password',
        description=(
            'Triggers a 6-digit OTP to be sent to the provided email address. '
            'The OTP expires in **2 minutes**. '
            'Any previously unused OTPs for this account are immediately invalidated.'
        ),
        request=ForgotPasswordSerializer,
        responses={
            200: OpenApiResponse(description='OTP sent (same response whether or not the email exists, to prevent enumeration)'),
            400: OpenApiResponse(description='Validation error'),
        },
        auth=[],
        tags=['Password Reset'],
    )
    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        otp_code = generate_otp()

        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)
        OTPCode.objects.create(user=user, code=otp_code)

        try:
            send_otp_email(user, otp_code)
        except Exception:
            pass

        return Response(
            {'detail': 'If an account with this email exists, an OTP has been sent.'},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """Verify that a password-reset OTP is valid before allowing the reset."""
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Verify OTP',
        description=(
            'Check that the submitted OTP is valid and has not expired. '
            'Call this before `reset-password` to confirm the code is correct. '
            'The OTP expires in **2 minutes**.'
        ),
        request=VerifyOTPSerializer,
        responses={
            200: OpenApiResponse(description='OTP is valid'),
            400: OpenApiResponse(description='Invalid or expired OTP'),
        },
        auth=[],
        tags=['Password Reset'],
    )
    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {'detail': 'OTP is valid. You may now reset your password.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """Reset the user's password using a valid OTP."""
    permission_classes = [AllowAny]

    @extend_schema(
        summary='Reset Password',
        description=(
            'Reset the account password. Requires the same email + OTP used in `forgot-password` / `verify-otp`. '
            "The new password must meet Django's password validation rules. "
            'After a successful reset, the OTP is invalidated and all other pending OTPs for this user are revoked.'
        ),
        request=ResetPasswordSerializer,
        responses={
            200: OpenApiResponse(description='Password reset successfully'),
            400: OpenApiResponse(description='Invalid/expired OTP or password validation failure'),
        },
        auth=[],
        tags=['Password Reset'],
    )
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Password has been reset successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )
