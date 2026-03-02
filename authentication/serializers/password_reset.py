from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from authentication.models import OTPCode, User


class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            user = User.objects.get(email=value, is_active=True)
        except User.DoesNotExist:
            # Do not reveal whether the email exists — still return silently
            raise serializers.ValidationError('No active account found with this email address.')
        self.user = user
        return value


class VerifyOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)

    def validate(self, attrs):
        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No active account found with this email address.'})

        otp = (
            OTPCode.objects
            .filter(user=user, code=otp_code, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if not otp:
            raise serializers.ValidationError({'otp_code': 'Invalid OTP code.'})

        if otp.is_expired:
            raise serializers.ValidationError({'otp_code': 'OTP code has expired. Please request a new one.'})

        attrs['user'] = user
        attrs['otp'] = otp
        return attrs


class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})

        email = attrs.get('email')
        otp_code = attrs.get('otp_code')

        try:
            user = User.objects.get(email=email, is_active=True)
        except User.DoesNotExist:
            raise serializers.ValidationError({'email': 'No active account found with this email address.'})

        otp = (
            OTPCode.objects
            .filter(user=user, code=otp_code, is_used=False)
            .order_by('-created_at')
            .first()
        )

        if not otp:
            raise serializers.ValidationError({'otp_code': 'Invalid OTP code.'})

        if otp.is_expired:
            raise serializers.ValidationError({'otp_code': 'OTP code has expired. Please request a new one.'})

        validate_password(attrs['new_password'], user)

        attrs['user'] = user
        attrs['otp'] = otp
        return attrs

    def save(self, **kwargs):
        user = self.validated_data['user']
        otp = self.validated_data['otp']

        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])

        otp.is_used = True
        otp.save(update_fields=['is_used'])

        # Invalidate all other unused OTPs for this user
        OTPCode.objects.filter(user=user, is_used=False).update(is_used=True)

        return user
