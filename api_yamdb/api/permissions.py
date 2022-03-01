from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.IsAuthenticated):

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.method in permissions.SAFE_METHODS
                or obj.author == request.user)


class IsAdminOrReadOnly(permissions.IsAdminUser):

    def has_permission(self, request, view):
        return ((request.user.is_authenticated
                and request.user.is_admin())
                or request.method in permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return ((request.user.is_authenticated
                and request.user.is_admin())
                or request.method in permissions.SAFE_METHODS)


class IsModeratorOrReadOnly(permissions.IsAdminUser):

    def has_permission(self, request, view):
        return ((request.user.is_authenticated
                and request.user.is_moderator())
                or request.method in permissions.SAFE_METHODS)

    def has_object_permission(self, request, view, obj):
        return ((request.user.is_authenticated
                and request.user.is_moderator())
                or request.method in permissions.SAFE_METHODS)


class IsOwnerOrIsAdmin(permissions.IsAdminUser):

    def has_permission(self, request, view):
        return (request.user.is_authenticated
                and request.user.is_admin())

    def has_object_permission(self, request, view, obj):
        return ((request.user.is_authenticated
                and request.user.is_admin())
                or obj.author == request.user)
