"""Tests for the RolePermission class and the permission model introspection.

These tests cover the edge cases where an API view uses a serializer which does
not define a Meta.model attribute (e.g. "action" endpoints which use a plain Serializer),
which previously caused the RolePermission check to "fail open".
"""

from django.contrib.auth.models import Group, User
from django.urls import URLPattern, URLResolver, get_resolver

from rest_framework import serializers
from rest_framework.request import ForcedAuthentication, Request
from rest_framework.settings import api_settings
from rest_framework.test import APIRequestFactory
from rest_framework.views import APIView

import InvenTree.permissions as permissions
from InvenTree.unit_test import InvenTreeTestCase


class PlainSerializer(serializers.Serializer):
    """Serializer with a Meta class, but no Meta.model attribute."""

    class Meta:
        """Meta options (no model)."""

        fields = ['value']

    value = serializers.IntegerField()


class NoMetaSerializer(serializers.Serializer):
    """Serializer without any Meta class."""

    value = serializers.IntegerField()


class GroupModelSerializer(serializers.ModelSerializer):
    """Serializer with a Meta.model attribute."""

    class Meta:
        """Meta options."""

        model = Group
        fields = ['pk']


class ModelIntrospectionTest(InvenTreeTestCase):
    """Unit tests for the get_model_for_view function and related helpers."""

    def test_serializer_model(self):
        """The model is extracted from the serializer_class attribute."""

        class View:
            serializer_class = GroupModelSerializer

        self.assertEqual(permissions.get_model_for_view(View()), Group)

    def test_missing_meta_model(self):
        """A serializer without Meta.model (or without Meta) raises PermissionModelNotFoundError."""
        for serializer_class in [PlainSerializer, NoMetaSerializer]:

            class View:
                pass

            View.serializer_class = serializer_class

            with self.assertRaises(permissions.PermissionModelNotFoundError):
                permissions.get_model_for_view(View())

            # Must remain compatible with callers which catch AttributeError
            with self.assertRaises(AttributeError):
                permissions.get_model_for_view(View())

    def test_no_serializer(self):
        """A view without any serializer raises PermissionModelNotFoundError."""

        class View:
            pass

        with self.assertRaises(permissions.PermissionModelNotFoundError):
            permissions.get_model_for_view(View())

    def test_serializer_class_none(self):
        """If serializer_class is None, get_serializer_class() is used instead."""

        class View:
            serializer_class = None

            def get_serializer_class(self):
                return GroupModelSerializer

        self.assertEqual(permissions.get_model_for_view(View()), Group)

    def test_get_serializer_class_errors(self):
        """Errors from DRF's default get_serializer_class() are handled."""

        class AssertView:
            serializer_class = None

            def get_serializer_class(self):
                # Mimic DRF GenericAPIView.get_serializer_class()
                raise AssertionError('serializer_class not set')

        class AttributeView:
            def get_serializer_class(self):
                raise AttributeError('no request')

        for view in [AssertView(), AttributeView()]:
            with self.assertRaises(permissions.PermissionModelNotFoundError):
                permissions.get_model_for_view(view)

    def test_get_permission_model(self):
        """get_permission_model() takes priority, and may explicitly return None."""

        class View:
            serializer_class = PlainSerializer

            def get_permission_model(self):
                return User

        self.assertEqual(permissions.get_model_for_view(View()), User)

        class OptOutView:
            serializer_class = GroupModelSerializer

            def get_permission_model(self):
                return None

        self.assertIsNone(permissions.get_model_for_view(OptOutView()))

    def test_queryset_model(self):
        """Test the queryset model fallback."""

        class View:
            queryset = User.objects.none()

        self.assertEqual(permissions.get_queryset_model_for_view(View()), User)

        class CachedView:
            queryset = None
            _cached_queryset = Group.objects.none()

        self.assertEqual(permissions.get_queryset_model_for_view(CachedView()), Group)

        class NoQuerysetView:
            pass

        self.assertIsNone(permissions.get_queryset_model_for_view(NoQuerysetView()))

    def test_roles_for_view(self):
        """get_roles_for_view falls back to the queryset model."""

        class View:
            serializer_class = PlainSerializer
            queryset = User.objects.none()

        roles = permissions.get_roles_for_view(View())
        self.assertIn('admin', roles)

        class NoModelView:
            serializer_class = PlainSerializer

        self.assertEqual(permissions.get_roles_for_view(NoModelView()), [])

    def test_split_role_required(self):
        """Test the split_role_required helper."""
        self.assertEqual(
            permissions.split_role_required('admin', 'view'), ('admin', 'view')
        )
        self.assertEqual(
            permissions.split_role_required('admin.add', 'view'), ('admin', 'add')
        )


class RolePermissionTest(InvenTreeTestCase):
    """Unit tests for RolePermission.has_permission against 'edge case' views."""

    roles = ['admin.view']

    def check(self, view_class, method: str) -> bool:
        """Run the RolePermission check for the given view class and HTTP method."""
        factory = APIRequestFactory()
        request = Request(
            getattr(factory, method.lower())('/'),
            authenticators=(ForcedAuthentication(self.user, None),),
        )
        return permissions.RolePermission().has_permission(request, view_class())

    def test_plain_serializer_with_queryset(self):
        """A plain serializer falls back to the queryset model for write operations."""

        class View:
            serializer_class = PlainSerializer
            queryset = User.objects.none()

        # Read access is not restricted
        self.assertTrue(self.check(View, 'GET'))

        # Write access requires the role permission against the queryset model
        for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            self.assertFalse(self.check(View, method))

        self.assignRole('admin.add')
        self.assertTrue(self.check(View, 'POST'))

    def test_plain_serializer_without_queryset(self):
        """If no model can be determined, write operations fail closed."""
        for serializer_class in [PlainSerializer, NoMetaSerializer, None]:

            class View:
                pass

            View.serializer_class = serializer_class

            self.assertTrue(self.check(View, 'GET'))

            for method in ['POST', 'PUT', 'PATCH', 'DELETE']:
                self.assertFalse(self.check(View, method))

    def test_superuser(self):
        """Superusers bypass the role checks."""

        class View:
            serializer_class = PlainSerializer

        self.user.is_superuser = True
        self.user.save()

        self.assertTrue(self.check(View, 'POST'))

    def test_explicit_opt_out(self):
        """A view can explicitly opt out of model permissions via get_permission_model."""

        class View:
            serializer_class = PlainSerializer

            def get_permission_model(self):
                return None

        self.assertTrue(self.check(View, 'POST'))

    def test_get_permission_model_error(self):
        """An unrelated AttributeError raised by the view is not swallowed."""

        class View:
            serializer_class = PlainSerializer
            queryset = Group.objects.none()

            def get_permission_model(self):
                raise AttributeError('Unexpected error')

        with self.assertRaises(AttributeError):
            self.check(View, 'POST')

    def test_role_required(self):
        """The role_required attribute takes priority over the model."""

        class View:
            serializer_class = GroupModelSerializer
            role_required = 'stock.add'

        # The model permission (admin role) is not sufficient
        self.assignRole('admin.add')
        self.assertFalse(self.check(View, 'POST'))

        self.assignRole('stock.add')
        self.assertTrue(self.check(View, 'POST'))


def get_api_views():
    """Return a list of (route, view_class) tuples for all DRF API views."""

    def walk(patterns, prefix=''):
        for pattern in patterns:
            if isinstance(pattern, URLResolver):
                yield from walk(pattern.url_patterns, prefix + str(pattern.pattern))
            elif isinstance(pattern, URLPattern):
                yield prefix + str(pattern.pattern), pattern.callback

    views = {}

    for route, callback in walk(get_resolver().url_patterns):
        view_class = getattr(callback, 'view_class', None) or getattr(
            callback, 'cls', None
        )

        if not route.startswith('api/') or view_class is None:
            continue

        if not issubclass(view_class, APIView):
            continue

        views.setdefault(view_class, route)

    return [(route, view_class) for view_class, route in views.items()]


class ApiViewPermissionModelTest(InvenTreeTestCase):
    """Ensure that every writable API view has a role or model to check against."""

    def test_writable_views_resolve_permission(self):
        """Every writable view protected by RolePermission must resolve a role or model.

        If no role or model can be determined, the RolePermission class denies
        all write operations (for non-superusers), which is likely a bug in the view.
        """
        errors = []

        for route, view_class in get_api_views():
            permission_classes = getattr(
                view_class,
                'permission_classes',
                api_settings.DEFAULT_PERMISSION_CLASSES,
            )

            if not any(
                isinstance(cls, type) and issubclass(cls, permissions.RolePermission)
                for cls in permission_classes
            ):
                continue

            methods = {
                m for m in ('post', 'put', 'patch', 'delete') if hasattr(view_class, m)
            } & set(getattr(view_class, 'http_method_names', []))

            if not methods:
                continue

            if getattr(view_class, 'role_required', None):
                continue

            if hasattr(view_class, 'get_permission_model'):
                continue

            view = view_class()

            try:
                permissions.get_model_for_view(view)
                continue
            except permissions.PermissionModelNotFoundError:
                pass

            if permissions.get_queryset_model_for_view(view) is None and not hasattr(
                view_class, 'get_queryset'
            ):
                errors.append(f'{route} ({view_class.__name__})')

        self.assertEqual(
            errors, [], 'API views without a resolvable permission model or role'
        )
