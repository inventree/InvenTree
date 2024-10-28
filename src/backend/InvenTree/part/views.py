"""Django views for interacting with Part app."""

from django.shortcuts import get_object_or_404

from InvenTree.helpers import str2bool
from InvenTree.views import AjaxView

from .bom import ExportBom, IsValidBOMFormat, MakeBomTemplate
from .models import Part


class BomUploadTemplate(AjaxView):
    """Provide a BOM upload template file for download.

    - Generates a template file in the provided format e.g. ?format=csv
    """

    def get(self, request, *args, **kwargs):
        """Perform a GET request to download the 'BOM upload' template."""
        export_format = request.GET.get('format', 'csv')

        return MakeBomTemplate(export_format)


class BomDownload(AjaxView):
    """Provide raw download of a BOM file.

    - File format should be passed as a query param e.g. ?format=csv
    """

    role_required = 'part.view'

    model = Part

    def get(self, request, *args, **kwargs):
        """Perform GET request to download BOM data."""
        part = get_object_or_404(Part, pk=self.kwargs['pk'])

        export_format = request.GET.get('format', 'csv')

        cascade = str2bool(request.GET.get('cascade', False))

        parameter_data = str2bool(request.GET.get('parameter_data', False))

        substitute_part_data = str2bool(request.GET.get('substitute_part_data', False))

        stock_data = str2bool(request.GET.get('stock_data', False))

        supplier_data = str2bool(request.GET.get('supplier_data', False))

        manufacturer_data = str2bool(request.GET.get('manufacturer_data', False))

        pricing_data = str2bool(request.GET.get('pricing_data', False))

        levels = request.GET.get('levels', None)

        if levels is not None:
            try:
                levels = int(levels)

                if levels <= 0:
                    levels = None

            except ValueError:
                levels = None

        if not IsValidBOMFormat(export_format):
            export_format = 'csv'

        return ExportBom(
            part,
            fmt=export_format,
            cascade=cascade,
            max_levels=levels,
            parameter_data=parameter_data,
            stock_data=stock_data,
            supplier_data=supplier_data,
            manufacturer_data=manufacturer_data,
            pricing_data=pricing_data,
            substitute_part_data=substitute_part_data,
        )

    def get_data(self):
        """Return a custom message."""
        return {'info': 'Exported BOM'}
