import random
import string
import uuid
from datetime import timedelta

import jwt
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.core.mail import send_mail


# ---------------------------------------------------------------------------
# Base model
# ---------------------------------------------------------------------------

class UUIDTimeStampedModel(models.Model):
    """
    Abstract base model that gives every subclass:
      - `id`         — UUID primary key (auto-generated, non-editable)
      - `created_at` — set once on creation
      - `updated_at` — updated on every save
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


# ---------------------------------------------------------------------------
# Invite JWT helpers
# ---------------------------------------------------------------------------

_INVITE_JWT_ALGORITHM = 'HS256'
_INVITE_JWT_EXPIRY_HOURS = 72  # Must match Invitation.expires_at default


def generate_invite_jwt(invitation, invited_by=None) -> str:
    """
    Generate a signed JWT invite token embedding:
      - invitation_id (str)
      - email
      - first_name
      - last_name
      - exp  (72 hours from now)

    The JWT is signed with Django's SECRET_KEY using HS256.
    """
    inviter = invited_by or invitation.invited_by
    payload = {
        'invitation_id': str(invitation.id),
        'email': invitation.email,
        'invited_by': {
            'first_name': inviter.first_name if inviter and inviter.first_name else '',
            'last_name': inviter.last_name if inviter and inviter.last_name else '',
        },
        'exp': timezone.now() + timedelta(hours=_INVITE_JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_INVITE_JWT_ALGORITHM)


def decode_invite_jwt(token: str) -> dict:
    """
    Decode and verify a JWT invite token.
    Returns the payload dict on success.
    Raises jwt.InvalidTokenError (or subclass) on failure.
    """
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_INVITE_JWT_ALGORITHM])




# ---------------------------------------------------------------------------
# OTP helpers
# ---------------------------------------------------------------------------

def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))


# ---------------------------------------------------------------------------
# Email helpers
# ---------------------------------------------------------------------------

def send_invite_email(invitation, request=None):
    """Send an invitation email with the accept-invite JWT link using Resend."""
    from authentication.utils import generate_invite_jwt  # local import to avoid circular
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    jwt_token = generate_invite_jwt(invitation)
    invite_url = f'{frontend_url}/accept-invite/?token={jwt_token}'

    if invitation.invited_by:
        inviter_name = invitation.invited_by.full_name or invitation.invited_by.email
    else:
        inviter_name = "Admin"
    subject = 'You have been invited to join Prime CRM'
    
    html_content = f"""
    <div style="font-family: sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #000;">Welcome to Prime CRM</h2>
        <p>Hello {invitation.email or ""},</p>
        <p>You have been invited by <strong>{inviter_name}</strong> to join <strong>Prime CRM</strong> as a <strong>{invitation.get_role_display()}</strong>.</p>
        <p>Click the button below to accept your invitation and set up your account:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{invite_url}" style="background-color: #000; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Accept Invitation</a>
        </div>
        <p style="font-size: 0.9em; color: #666;">This invitation will expire in 72 hours. If you did not expect this invitation, you can safely ignore this email.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 0.8em; color: #999;">Best regards,<br>The Prime CRM Team</p>
    </div>
    """

    send_mail(
        subject=subject,
        message="Please view this email in an HTML-compatible client.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
        html_message=html_content,
        fail_silently=False,
    )


def send_welcome_email(user):
    """Send a welcome email after successfully accepting an invitation."""
    subject = 'Welcome to Prime CRM!'
    
    html_content = f"""
    <div style="font-family: sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #eee; border-radius: 10px;">
        <h2 style="color: #000;">Account Created Successfully</h2>
        <p>Hello {user.first_name or user.email},</p>
        <p>Your account on <strong>Prime CRM</strong> has been successfully created. You can now log in and start managing your workspace.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')}/login" style="background-color: #000; color: #fff; padding: 12px 24px; text-decoration: none; border-radius: 5px; font-weight: bold;">Go to Dashboard</a>
        </div>
        <p>If you have any questions, feel free to reply to this email.</p>
        <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;" />
        <p style="font-size: 0.8em; color: #999;">Best regards,<br>The Prime CRM Team</p>
    </div>
    """

    send_mail(
        subject=subject,
        message="Please view this email in an HTML-compatible client.",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        html_message=html_content,
        fail_silently=False,
    )


def send_otp_email(user, otp_code: str):
    """Send a password-reset OTP to the user's email."""
    subject = 'Prime CRM — Password Reset OTP'
    message = (
        f'Hello {user.full_name or user.email},\n\n'
        f'Your password reset OTP is:\n\n'
        f'    {otp_code}\n\n'
        f'This code is valid for 2 minutes. Do not share it with anyone.\n\n'
        f'If you did not request a password reset, please ignore this email.\n\n'
        f'Best regards,\nPrime CRM Team'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
