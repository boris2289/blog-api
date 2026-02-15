from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerorReadOnly(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        return obj.author.id == request.user.id
