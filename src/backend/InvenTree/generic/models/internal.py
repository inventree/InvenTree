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


class ContentTypeMixin:
    """Mixin class which supports retrieval of the ContentType for a model instance."""

    @classmethod
    def get_content_type(cls):
        """Return the ContentType object associated with this model."""
        from django.contrib.contenttypes.models import ContentType

        return ContentType.objects.get_for_model(cls)


class DiffMixin:
    """Mixin which can be used to determine which fields have changed, compared to the instance saved to the database."""

    def get_db_instance(self):
        """Return the instance of the object saved in the database.

        Returns:
            object: Instance of the object saved in the database
        """
        if self.pk:
            try:
                return self.__class__.objects.get(pk=self.pk)
            except self.__class__.DoesNotExist:
                pass

        return None

    def get_field_deltas(self):
        """Return a dict of field deltas.

        Compares the current instance with the instance saved in the database,
        and returns a dict of fields which have changed.

        Returns:
            dict: Dict of field deltas
        """
        db_instance = self.get_db_instance()

        if db_instance is None:
            return {}

        deltas = {}

        for field in self._meta.fields:
            if field.name == 'id':
                continue

            if field.is_relation:
                # Compare the raw FK id first (no query) - only dereference to the
                # full related object (one query each side) if it actually differs.
                # In the common case (unchanged FK) this avoids two full-object
                # fetches per relational field for every single save() call.
                if getattr(self, field.attname) == getattr(db_instance, field.attname):
                    continue

            if getattr(self, field.name) != getattr(db_instance, field.name):
                deltas[field.name] = {
                    'old': getattr(db_instance, field.name),
                    'new': getattr(self, field.name),
                }

        return deltas

    def has_field_changed(self, field_name):
        """Determine if a particular field has changed."""
        return field_name in self.get_field_deltas()
