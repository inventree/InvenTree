"""Helpers for controlling admin interface permissions."""


class NoAddAdminMixin:
    """Mixin to prevent addition of new objects via the admin interface."""

    def has_add_permission(self, request, obj=None):
        """Prevent addition of new objects via the admin interface."""
        return False


class NoEditAdminMixin(NoAddAdminMixin):
    """Base admin class that prevents editing of objects."""

    def has_change_permission(self, request, obj=None):
        """Prevent modification of objects via the admin interface."""
        return False


class ReadOnlyAdminMixin(NoEditAdminMixin):
    """Base admin class that prevents all modifications."""

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of objects via the admin interface."""
        return False
