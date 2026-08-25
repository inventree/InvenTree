"""URL patterns for the SCIM 2.0 provisioning endpoint (`/scim/v2/...`)."""

from django.urls import path, re_path

from scim.views import (
    GroupDetailView,
    GroupsView,
    ResourceTypesView,
    SchemasView,
    ScimNotFoundView,
    ServiceProviderConfigView,
    UserDetailView,
    UsersView,
)

scim_urls = [
    path(
        'ServiceProviderConfig',
        ServiceProviderConfigView.as_view(),
        name='scim-service-provider-config',
    ),
    path('ResourceTypes', ResourceTypesView.as_view(), name='scim-resource-types'),
    path(
        'ResourceTypes/<str:name>',
        ResourceTypesView.as_view(),
        name='scim-resource-type-detail',
    ),
    path('Schemas', SchemasView.as_view(), name='scim-schemas'),
    path('Schemas/<str:schema_id>', SchemasView.as_view(), name='scim-schema-detail'),
    path('Users', UsersView.as_view(), name='scim-users'),
    path('Users/<int:pk>', UserDetailView.as_view(), name='scim-user-detail'),
    path('Groups', GroupsView.as_view(), name='scim-groups'),
    path('Groups/<int:pk>', GroupDetailView.as_view(), name='scim-group-detail'),
]

urlpatterns = scim_urls + [re_path(r'^(?P<path>.*)$', ScimNotFoundView.as_view())]  # noqa: RUF005
