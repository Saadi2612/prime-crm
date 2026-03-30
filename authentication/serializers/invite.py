import jwt
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from authentication.models import Invitation, User
from authentication.utils import decode_invite_jwt


class InviteUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = Invitation
        fields = ['email', 'phone_number', 'role']

    def validate_role(self, value):
        requester = self.context['request'].user

        if requester.role == User.Role.ADMIN:
            if value not in (User.Role.MANAGER, User.Role.AGENT):
                raise serializers.ValidationError(
                    'Admin can only invite Managers or Agents.'
                )
        elif requester.role == User.Role.MANAGER:
            if value != User.Role.AGENT:
                raise serializers.ValidationError(
                    'Managers can only invite Agents.'
                )
        else:
            raise serializers.ValidationError(
                'You do not have permission to invite users.'
            )
        return value

    def validate_email(self, value):
        value = value.lower()
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
    first_name = serializers.CharField(max_length=150)
    last_name = serializers.CharField(max_length=150)
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    confirm_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    token = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({'confirm_password': 'Passwords do not match.'})
        validate_password(attrs['password'])
        return attrs

    def validate_token(self, value):
        try:
            payload = decode_invite_jwt(value)
        except jwt.ExpiredSignatureError:
            raise serializers.ValidationError('This invitation link has expired.')
        except jwt.InvalidTokenError:
            raise serializers.ValidationError('Invalid invitation token.')

        invitation_id = payload.get('invitation_id')
        try:
            invitation = Invitation.objects.get(id=invitation_id)
        except Invitation.DoesNotExist:
            raise serializers.ValidationError('Invitation not found.')

        if invitation.is_used:
            raise serializers.ValidationError('This invitation has already been used.')

        # Double-check the DB-level expiry as well (in case someone bypasses JWT exp)
        if invitation.is_expired:
            raise serializers.ValidationError('This invitation has expired.')

        # Stash for use in save()
        self._invitation = invitation
        self._payload = payload
        return value

    def save(self, **kwargs):
        invitation = self._invitation
        payload = self._payload

        user = User.objects.create_user(
            email=invitation.email,
            password=self.validated_data['password'],
            first_name=self.validated_data.get('first_name', ''),
            last_name=self.validated_data.get('last_name', ''),
            phone_number=self.validated_data.get('phone_number') or invitation.phone_number,
            role=invitation.role,
        )

        invitation.is_used = True
        invitation.save(update_fields=['is_used'])
        return user


class PendingInvitationSerializer(serializers.ModelSerializer):
    invited_by_email = serializers.EmailField(source='invited_by.email', read_only=True)

    class Meta:
        model = Invitation
        fields = [
            'id',
            'email',
            'phone_number',
            'role',
            'invited_by_email',
            'created_at',
            'expires_at',
            'is_expired'
        ]
