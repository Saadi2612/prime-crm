from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from authentication.models import User


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        user = authenticate(request=self.context.get('request'), username=email, password=password)

        if not user:
            raise serializers.ValidationError('Invalid email or password.', code='authorization')

        if not user.is_active:
            raise serializers.ValidationError('This account has been deactivated.', code='authorization')

        attrs['user'] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'New passwords do not match.'})
        validate_password(attrs['new_password'], self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    lead_stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone_number', 'first_name', 'last_name',
            'full_name', 'role', 'is_active', 'date_joined', 'lead_stats',
        ]
        read_only_fields = fields

    def get_lead_stats(self, obj):
        return {
            'total': getattr(obj, 'total_leads_count', 0),
            'active': getattr(obj, 'active_leads_count', 0),
            'won': getattr(obj, 'won_leads_count', 0),
            'lost': getattr(obj, 'lost_leads_count', 0),
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    """Serializer for a user to update their own profile (non-sensitive fields only)."""

    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number']
