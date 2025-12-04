"""API views for supplier plugins in InvenTree."""

from typing import TYPE_CHECKING

from django.db import transaction
from django.urls import path

from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.exceptions import NotFound
from rest_framework.response import Response
from rest_framework.views import APIView

from InvenTree import permissions
from part.models import PartCategoryParameterTemplate
from plugin import registry
from plugin.plugin import PluginMixinEnum

from .serializers import (
    ImportRequestSerializer,
    ImportResultSerializer,
    SearchResultSerializer,
    SupplierListSerializer,
)

if TYPE_CHECKING:
    from plugin.base.supplier.mixins import SupplierMixin
else:  # pragma: no cover

    class SupplierMixin:
        """Dummy class for type checking."""


def get_supplier_plugin(plugin_slug: str, supplier_slug: str) -> SupplierMixin:
    """Return the supplier plugin for the given plugin and supplier slugs."""
    supplier_plugin = None
    for plugin in registry.with_mixin(PluginMixinEnum.SUPPLIER):
        if plugin.slug == plugin_slug:
            supplier_plugin = plugin
            break

    if not supplier_plugin:
        raise NotFound(detail=f"Plugin '{plugin_slug}' not found")

    if not any(s.slug == supplier_slug for s in supplier_plugin.get_suppliers()):
        raise NotFound(
            detail=f"Supplier '{supplier_slug}' not found for plugin '{plugin_slug}'"
        )

    return supplier_plugin


class ListSupplier(APIView):
    """List all available supplier plugins.

    - GET: List supplier plugins
    """

    role_required = 'part.add'
    permission_classes = [
        permissions.IsAuthenticatedOrReadScope,
        permissions.RolePermission,
    ]
    serializer_class = SupplierListSerializer

    @extend_schema(responses={200: SupplierListSerializer(many=True)})
    def get(self, request):
        """List all available supplier plugins."""
        suppliers = []
        for plugin in registry.with_mixin(PluginMixinEnum.SUPPLIER):
            suppliers.extend([
                {
                    'plugin_slug': plugin.slug,
                    'supplier_slug': supplier.slug,
                    'supplier_name': supplier.name,
                }
                for supplier in plugin.get_suppliers()
            ])

        return Response(suppliers)


class SearchPart(APIView):
    """Search parts by supplier.

    - GET: Start part search
    """

    role_required = 'part.add'
    permission_classes = [
        permissions.IsAuthenticatedOrReadScope,
        permissions.RolePermission,
    ]
    serializer_class = SearchResultSerializer

    @extend_schema(
        parameters=[
            OpenApiParameter(name='plugin', description='Plugin slug', required=True),
            OpenApiParameter(
                name='supplier', description='Supplier slug', required=True
            ),
            OpenApiParameter(name='term', description='Search term', required=True),
        ],
        responses={200: SearchResultSerializer(many=True)},
    )
    def get(self, request):
        """Search parts by supplier."""
        plugin_slug = request.query_params.get('plugin', '')
        supplier_slug = request.query_params.get('supplier', '')
        term = request.query_params.get('term', '')

        supplier_plugin = get_supplier_plugin(plugin_slug, supplier_slug)
        try:
            results = supplier_plugin.get_search_results(supplier_slug, term)
        except Exception as e:
            return Response(
                {'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        response = SearchResultSerializer(results, many=True).data
        return Response(response)


class ImportPart(APIView):
    """Import a part by supplier.

    - POST: Attempt to import part by sku
    """

    role_required = 'part.add'
    permission_classes = [
        permissions.IsAuthenticatedOrReadScope,
        permissions.RolePermission,
    ]
    serializer_class = ImportResultSerializer

    @extend_schema(
        request=ImportRequestSerializer, responses={200: ImportResultSerializer}
    )
    def post(self, request):
        """Import a part by supplier."""
        serializer = ImportRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        # Extract validated data
        plugin_slug = serializer.validated_data.get('plugin', '')
        supplier_slug = serializer.validated_data.get('supplier', '')
        part_import_id = serializer.validated_data.get('part_import_id', '')
        category = serializer.validated_data.get('category_id', None)
        part = serializer.validated_data.get('part_id', None)

        supplier_plugin = get_supplier_plugin(plugin_slug, supplier_slug)

        # Validate part/category
        if not part and not category:
            return Response(
                {
                    'detail': "'category_id' is not provided, but required if no part_id is provided"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from plugin.base.supplier.mixins import supplier

        # Import part data
        try:
            import_data = supplier_plugin.get_import_data(supplier_slug, part_import_id)

            with transaction.atomic():
                # create part if it does not exist
                if not part:
                    part = supplier_plugin.import_part(
                        import_data, category=category, creation_user=request.user
                    )

                # create manufacturer part
                manufacturer_part = supplier_plugin.import_manufacturer_part(
                    import_data, part=part
                )

                # create supplier part
                supplier_part = supplier_plugin.import_supplier_part(
                    import_data, part=part, manufacturer_part=manufacturer_part
                )

                # set default supplier if not set
                if not part.default_supplier:
                    part.default_supplier = supplier_part
                    part.save()

                # get pricing
                pricing = supplier_plugin.get_pricing_data(import_data)

                # get parameters
                parameters = supplier_plugin.get_parameters(import_data)
        except supplier.PartNotFoundError:
            return Response(
                {'detail': f"Part with id: '{part_import_id}' not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {'detail': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # add default parameters for category
        if category:
            categories = category.get_ancestors(include_self=True)
            category_parameters = PartCategoryParameterTemplate.objects.filter(
                category__in=categories
            )

            for c in category_parameters:
                for p in parameters:
                    if p.parameter_template == c.template:
                        p.on_category = True
                        p.value = p.value if p.value is not None else c.default_value
                        break
                else:
                    parameters.append(
                        supplier.ImportParameter(
                            name=c.template.name,
                            value=c.default_value,
                            on_category=True,
                            parameter_template=c.template,
                        )
                    )
            parameters.sort(key=lambda x: x.on_category, reverse=True)

        response = ImportResultSerializer({
            'part_id': part.pk,
            'part_detail': part,
            'supplier_part_id': supplier_part.pk,
            'manufacturer_part_id': manufacturer_part.pk,
            'pricing': pricing,
            'parameters': parameters,
        }).data
        return Response(response)


supplier_api_urls = [
    path('list/', ListSupplier.as_view(), name='api-supplier-list'),
    path('search/', SearchPart.as_view(), name='api-supplier-search'),
    path('import/', ImportPart.as_view(), name='api-supplier-import'),
]
