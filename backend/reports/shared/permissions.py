"""Cross-cutting DRF permissions shared by feature modules."""

from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdminOrReadOnly(BasePermission):
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return bool(request.user and request.user.is_authenticated)
        return bool(request.user and request.user.is_staff)


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return bool(request.user and (request.user.is_staff or obj.created_by_id == request.user.id))
