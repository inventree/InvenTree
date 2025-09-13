"""API views for supplier plugins in InvenTree."""

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
)


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
            OpenApiParameter(
                name='supplier', description='Supplier slug', required=True
            ),
            OpenApiParameter(name='term', description='Search term', required=True),
        ],
        responses={200: SearchResultSerializer(many=True)},
    )
    def get(self, request):
        """Search parts by supplier."""
        supplier_slug = request.query_params.get('supplier', '')

        supplier = None
        for plugin in registry.with_mixin(PluginMixinEnum.SUPPLIER):
            if plugin.slug == supplier_slug:
                supplier = plugin
                break

        if not supplier:
            raise NotFound(detail=f"Supplier '{supplier_slug}' not found")

        term = request.query_params.get('term', '')
        try:
            results = supplier.get_search_results(term)
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
        supplier_slug = serializer.validated_data.get('supplier', '')
        part_import_id = serializer.validated_data.get('part_import_id', None)
        category = serializer.validated_data.get('category_id', None)
        part = serializer.validated_data.get('part_id', None)

        # Find the supplier plugin
        supplier = None
        for plugin in registry.with_mixin(PluginMixinEnum.SUPPLIER):
            if plugin.slug == supplier_slug:
                supplier = plugin
                break

        # Validate supplier and part/category
        if not supplier:
            raise NotFound(detail=f"Supplier '{supplier_slug}' not found")
        if not part and not category:
            return Response(
                {
                    'detail': "'category_id' is not provided, but required if no part_id is provided"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        from plugin.base.supplier.mixins import SupplierMixin

        # Import part data
        try:
            import_data = supplier.get_import_data(part_import_id)

            with transaction.atomic():
                # create part if it does not exist
                if not part:
                    part = supplier.import_part(
                        import_data, category=category, creation_user=request.user
                    )

                # create manufacturer part
                manufacturer_part = supplier.import_manufacturer_part(
                    import_data, part=part
                )

                # create supplier part
                supplier_part = supplier.import_supplier_part(
                    import_data, part=part, manufacturer_part=manufacturer_part
                )

                # set default supplier if not set
                if not part.default_supplier:
                    part.default_supplier = supplier_part
                    part.save()

                # get pricing
                pricing = supplier.get_pricing_data(import_data)

                # get parameters
                parameters = supplier.get_parameters(import_data)
        except SupplierMixin.PartNotFoundError:
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
                    if p.parameter_template == c.parameter_template:
                        p.on_category = True
                        p.value = p.value if p.value is not None else c.default_value
                        break
                else:
                    parameters.append(
                        SupplierMixin.ImportParameter(
                            name=c.parameter_template.name,
                            value=c.default_value,
                            on_category=True,
                            parameter_template=c.parameter_template,
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
    path('search/', SearchPart.as_view(), name='api-supplier-search'),
    path('import/', ImportPart.as_view(), name='api-supplier-import'),
]
