from rest_framework.permissions import BasePermission


class IsAdmin(BasePermission):
    """Allow access only to users with the Admin role."""
    message = 'Only Admins are allowed to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'admin'
        )


class IsManager(BasePermission):
    """Allow access only to users with the Manager role."""
    message = 'Only Managers are allowed to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == 'manager'
        )


class IsAdminOrManager(BasePermission):
    """Allow access to users with Admin or Manager roles."""
    message = 'Only Admins or Managers are allowed to perform this action.'

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ('admin', 'manager')
        )
