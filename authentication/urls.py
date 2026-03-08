from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from authentication.views.auth import LoginView, LogoutView, ChangePasswordView, MeView
from authentication.views.invite import (
    InviteUserView, AcceptInviteView,
    PendingInvitationListView, PendingInvitationDetailView, ResendInvitationView
)
from authentication.views.password_reset import ForgotPasswordView, VerifyOTPView, ResetPasswordView
from authentication.views.user import UserListView, UpdateMeView

app_name = 'authentication'

urlpatterns = [
    # ── Auth ────────────────────────────────────────────────────────
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('change-password/', ChangePasswordView.as_view(), name='change-password'),
    path('me/', MeView.as_view(), name='me'),
    path('me/update/', UpdateMeView.as_view(), name='me-update'),

    # ── Users ────────────────────────────────────────────────────────
    path('users/', UserListView.as_view(), name='user-list'),

    # ── Invitations ──────────────────────────────────────────────────
    path('invite/', InviteUserView.as_view(), name='invite'),
    path('accept-invite/', AcceptInviteView.as_view(), name='accept-invite'),
    path('invitations/pending/', PendingInvitationListView.as_view(), name='pending-invitation-list'),
    path('invitations/<uuid:pk>/', PendingInvitationDetailView.as_view(), name='pending-invitation-detail'),
    path('invitations/<uuid:pk>/resend/', ResendInvitationView.as_view(), name='resend-invitation'),

    # ── Password Reset ───────────────────────────────────────────────
    path('forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]
