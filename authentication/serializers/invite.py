from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from authentication.models import Invitation, User


class InviteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['email', 'phone_number', 'role']

    def validate_role(self, value):
        requester = self.context['request'].user

        if requester.role == 'admin':
            if value not in ('manager', 'agent'):
                raise serializers.ValidationError(
                    'Admin can only invite Managers or Agents.'
                )
        elif requester.role == 'manager':
            if value != 'agent':
                raise serializers.ValidationError(
                    'Managers can only invite Agents.'
                )
        else:
            raise serializers.ValidationError(
                'You do not have permission to invite users.'
            )
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError(
                'A user with this email already exists.'
            )
        if Invitation.objects.filter(email=value, is_used=False).exists():
            raise serializers.ValidationError(
                'An active invitation has already been sent to this email.'
            )
        return value

    def create(self, validated_data):
        invitation = Invitation.objects.create(
            invited_by=self.context['request'].user,
            **validated_data,
        )
        return invitation


class AcceptInviteSerializer(serializers.Serializer):
    token = serializers.UUIDField()
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        return attrs

    def validate_token(self, value):
        try:
            invitation = Invitation.objects.get(token=value)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError('Invalid invitation token.')

        if invitation.is_used:
            raise serializers.ValidationError('This invitation has already been used.')

        if invitation.is_expired:
            raise serializers.ValidationError('This invitation has expired.')

        self.invitation = invitation
        return value

    def save(self, **kwargs):
        invitation = self.invitation
        user = User.objects.create_user(
            email=invitation.email,
            password=self.validated_data['password'],
            first_name=self.validated_data['first_name'],
            last_name=self.validated_data['last_name'],
            phone_number=self.validated_data.get('phone_number') or invitation.phone_number,
            role=invitation.role,
        )
        invitation.is_used = True
        invitation.save(update_fields=['is_used'])
        return user
