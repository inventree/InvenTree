"""Internal model mixins for building InvenTree models."""


class InvenTreePermissionCheckMixin:
    """Provides an abstracted class for managing permissions against related fields."""

    @classmethod
    def check_related_permission(cls, permission, user) -> bool:
        """Check if the user has permission to perform the specified action on the attachment.

        The default implementation runs a permission check against *this* model class,
        but this can be overridden in the implementing class if required.

        Arguments:
            permission: The permission to check (add / change / view / delete)
            user: The user to check against

        Returns:
            bool: True if the user has permission, False otherwise
        """
        perm = f'{cls._meta.app_label}.{permission}_{cls._meta.model_name}'
        return user.has_perm(perm)
