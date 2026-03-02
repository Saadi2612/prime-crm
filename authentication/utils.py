import random
import string

from django.conf import settings
from django.core.mail import send_mail


def generate_otp(length: int = 6) -> str:
    """Generate a numeric OTP of given length."""
    return ''.join(random.choices(string.digits, k=length))


def send_invite_email(invitation, request=None):
    """Send an invitation email with the accept-invite link."""
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    invite_url = f'{frontend_url}/accept-invite/?token={invitation.token}'

    subject = 'You have been invited to Prime CRM'
    message = (
        f'Hello,\n\n'
        f'You have been invited by {invitation.invited_by.full_name} to join Prime CRM '
        f'as a {invitation.get_role_display()}.\n\n'
        f'Click the link below to accept your invitation and set up your account:\n'
        f'{invite_url}\n\n'
        f'This invitation will expire in 72 hours.\n\n'
        f'If you did not expect this invitation, you can safely ignore this email.\n\n'
        f'Best regards,\nPrime CRM Team'
    )

    send_mail(
        subject=subject,
        message=message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[invitation.email],
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
