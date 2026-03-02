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
    """
    POST /auth/forgot-password/
    Generate and email a 6-digit OTP to the user for password reset.
    """

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.user
        otp_code = generate_otp()

        # Invalidate all previous unused OTPs for this user
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        # Create new OTP
        OTPCode.objects.create(user=user, code=otp_code)

        try:
            send_otp_email(user, otp_code)
        except Exception:
            # Don't expose email sending failures to the client
            pass

        return Response(
            {'detail': 'If an account with this email exists, an OTP has been sent.'},
            status=status.HTTP_200_OK,
        )


class VerifyOTPView(APIView):
    """
    POST /auth/verify-otp/
    Verify that the submitted OTP is valid and not expired.
    Returns a success flag that the frontend can use to enable the reset form.
    """

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        return Response(
            {'detail': 'OTP is valid. You may now reset your password.'},
            status=status.HTTP_200_OK,
        )


class ResetPasswordView(APIView):
    """
    POST /auth/reset-password/
    Reset user password after verifying the OTP.
    """

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(
            {'detail': 'Password has been reset successfully. You can now log in.'},
            status=status.HTTP_200_OK,
        )
