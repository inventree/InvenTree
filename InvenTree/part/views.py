"""Django views for interacting with Part app."""

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.shortcuts import HttpResponseRedirect, get_object_or_404
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView

from common.files import FileManager
from common.views import FileManagementAjaxView, FileManagementFormView
from company.models import SupplierPart
from InvenTree.helpers import str2bool
from InvenTree.views import AjaxView, InvenTreeRoleMixin, QRCodeView
from stock.models import StockItem, StockLocation

from . import settings as part_settings
from .bom import ExportBom, IsValidBOMFormat, MakeBomTemplate
from .models import Part, PartCategory


class PartImport(FileManagementFormView):
    """Part: Upload file, match to fields and import parts(using multi-Step form)"""
    permission_required = 'part.add'

    class PartFileManager(FileManager):
        """Import field definitions"""
        REQUIRED_HEADERS = [
            'Name',
            'Description',
        ]

        OPTIONAL_MATCH_HEADERS = [
            'Category',
            'default_location',
            'default_supplier',
            'variant_of',
        ]

        OPTIONAL_HEADERS = [
            'Keywords',
            'IPN',
            'Revision',
            'Link',
            'default_expiry',
            'minimum_stock',
            'Units',
            'Notes',
            'Active',
            'base_cost',
            'Multiple',
            'Assembly',
            'Component',
            'is_template',
            'Purchaseable',
            'Salable',
            'Trackable',
            'Virtual',
            'Stock',
        ]

    name = 'part'
    form_steps_template = [
        'part/import_wizard/part_upload.html',
        'part/import_wizard/match_fields.html',
        'part/import_wizard/match_references.html',
    ]
    form_steps_description = [
        _("Upload File"),
        _("Match Fields"),
        _("Match References"),
    ]

    form_field_map = {
        'name': 'name',
        'description': 'description',
        'keywords': 'keywords',
        'ipn': 'ipn',
        'revision': 'revision',
        'link': 'link',
        'default_expiry': 'default_expiry',
        'minimum_stock': 'minimum_stock',
        'units': 'units',
        'notes': 'notes',
        'category': 'category',
        'default_location': 'default_location',
        'default_supplier': 'default_supplier',
        'variant_of': 'variant_of',
        'active': 'active',
        'base_cost': 'base_cost',
        'multiple': 'multiple',
        'assembly': 'assembly',
        'component': 'component',
        'is_template': 'is_template',
        'purchaseable': 'purchaseable',
        'salable': 'salable',
        'trackable': 'trackable',
        'virtual': 'virtual',
        'stock': 'stock',
    }
    file_manager_class = PartFileManager

    def get_field_selection(self):
        """Fill the form fields for step 3."""
        # fetch available elements
        self.allowed_items = {}
        self.matches = {}

        self.allowed_items['Category'] = PartCategory.objects.all()
        self.matches['Category'] = ['name__contains']
        self.allowed_items['default_location'] = StockLocation.objects.all()
        self.matches['default_location'] = ['name__contains']
        self.allowed_items['default_supplier'] = SupplierPart.objects.all()
        self.matches['default_supplier'] = ['SKU__contains']
        self.allowed_items['variant_of'] = Part.objects.all()
        self.matches['variant_of'] = ['name__contains']

        # setup
        self.file_manager.setup()
        # collect submitted column indexes
        col_ids = {}
        for col in self.file_manager.HEADERS:
            index = self.get_column_index(col)
            if index >= 0:
                col_ids[col] = index

        # parse all rows
        for row in self.rows:
            # check each submitted column
            for idx in col_ids:
                data = row['data'][col_ids[idx]]['cell']

                if idx in self.file_manager.OPTIONAL_MATCH_HEADERS:
                    try:
                        exact_match = self.allowed_items[idx].get(**{a: data for a in self.matches[idx]})
                    except (ValueError, self.allowed_items[idx].model.DoesNotExist, self.allowed_items[idx].model.MultipleObjectsReturned):
                        exact_match = None

                    row['match_options_' + idx] = self.allowed_items[idx]
                    row['match_' + idx] = exact_match
                    continue

                # general fields
                row[idx.lower()] = data

    def done(self, form_list, **kwargs):
        """Create items."""
        items = self.get_clean_items()

        import_done = 0
        import_error = []

        # Create Part instances
        for part_data in items.values():

            # set related parts
            optional_matches = {}
            for idx in self.file_manager.OPTIONAL_MATCH_HEADERS:
                if idx.lower() in part_data:
                    try:
                        optional_matches[idx] = self.allowed_items[idx].get(pk=int(part_data[idx.lower()]))
                    except (ValueError, self.allowed_items[idx].model.DoesNotExist, self.allowed_items[idx].model.MultipleObjectsReturned):
                        optional_matches[idx] = None
                else:
                    optional_matches[idx] = None

            # add part
            new_part = Part(
                name=part_data.get('name', ''),
                description=part_data.get('description', ''),
                keywords=part_data.get('keywords', None),
                IPN=part_data.get('ipn', None),
                revision=part_data.get('revision', None),
                link=part_data.get('link', None),
                default_expiry=part_data.get('default_expiry', 0),
                minimum_stock=part_data.get('minimum_stock', 0),
                units=part_data.get('units', None),
                notes=part_data.get('notes', None),
                category=optional_matches['Category'],
                default_location=optional_matches['default_location'],
                default_supplier=optional_matches['default_supplier'],
                variant_of=optional_matches['variant_of'],
                active=str2bool(part_data.get('active', True)),
                base_cost=part_data.get('base_cost', 0),
                multiple=part_data.get('multiple', 1),
                assembly=str2bool(part_data.get('assembly', part_settings.part_assembly_default())),
                component=str2bool(part_data.get('component', part_settings.part_component_default())),
                is_template=str2bool(part_data.get('is_template', part_settings.part_template_default())),
                purchaseable=str2bool(part_data.get('purchaseable', part_settings.part_purchaseable_default())),
                salable=str2bool(part_data.get('salable', part_settings.part_salable_default())),
                trackable=str2bool(part_data.get('trackable', part_settings.part_trackable_default())),
                virtual=str2bool(part_data.get('virtual', part_settings.part_virtual_default())),
            )
            try:
                new_part.save()

                # add stock item if set
                if part_data.get('stock', None):
                    stock = StockItem(
                        part=new_part,
                        location=new_part.default_location,
                        quantity=int(part_data.get('stock', 1)),
                    )
                    stock.save()
                import_done += 1
            except ValidationError as _e:
                import_error.append(', '.join(set(_e.messages)))

        # Set alerts
        if import_done:
            alert = f"<strong>{_('Part-Import')}</strong><br>{_('Imported {n} parts').format(n=import_done)}"
            messages.success(self.request, alert)
        if import_error:
            error_text = '\n'.join([f'<li><strong>x{import_error.count(a)}</strong>: {a}</li>' for a in set(import_error)])
            messages.error(self.request, f"<strong>{_('Some errors occured:')}</strong><br><ul>{error_text}</ul>")

        return HttpResponseRedirect(reverse('part-index'))


class PartImportAjax(FileManagementAjaxView, PartImport):
    """Multi-step form wizard for importing Part data"""
    ajax_form_steps_template = [
        'part/import_wizard/ajax_part_upload.html',
        'part/import_wizard/ajax_match_fields.html',
        'part/import_wizard/ajax_match_references.html',
    ]

    def validate(self, obj, form, **kwargs):
        """Validation is performed based on the current form step"""
        return PartImport.validate(self, self.steps.current, form, **kwargs)


class PartQRCode(QRCodeView):
    """View for displaying a QR code for a Part object."""

    ajax_form_title = _("Part QR Code")

    role_required = 'part.view'

    def get_qr_data(self):
        """Generate QR code data for the Part."""
        try:
            part = Part.objects.get(id=self.pk)
            return part.format_barcode()
        except Part.DoesNotExist:
            return None


class BomUpload(InvenTreeRoleMixin, DetailView):
    """View for uploading a BOM file, and handling BOM data importing."""

    context_object_name = 'part'
    queryset = Part.objects.all()
    template_name = 'part/upload_bom.html'


class BomUploadTemplate(AjaxView):
    """Provide a BOM upload template file for download.

    - Generates a template file in the provided format e.g. ?format=csv
    """

    def get(self, request, *args, **kwargs):
        """Perform a GET request to download the 'BOM upload' template"""
        export_format = request.GET.get('format', 'csv')

        return MakeBomTemplate(export_format)


class BomDownload(AjaxView):
    """Provide raw download of a BOM file.

    - File format should be passed as a query param e.g. ?format=csv
    """

    role_required = 'part.view'

    model = Part

    def get(self, request, *args, **kwargs):
        """Perform GET request to download BOM data"""
        part = get_object_or_404(Part, pk=self.kwargs['pk'])

        export_format = request.GET.get('format', 'csv')

        cascade = str2bool(request.GET.get('cascade', False))

        parameter_data = str2bool(request.GET.get('parameter_data', False))

        stock_data = str2bool(request.GET.get('stock_data', False))

        supplier_data = str2bool(request.GET.get('supplier_data', False))

        manufacturer_data = str2bool(request.GET.get('manufacturer_data', False))

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

        return ExportBom(part,
                         fmt=export_format,
                         cascade=cascade,
                         max_levels=levels,
                         parameter_data=parameter_data,
                         stock_data=stock_data,
                         supplier_data=supplier_data,
                         manufacturer_data=manufacturer_data,
                         )

    def get_data(self):
        """Return a cutsom message"""
        return {
            'info': 'Exported BOM'
        }
