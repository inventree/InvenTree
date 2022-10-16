"""Django views for interacting with Company app."""

from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from InvenTree.views import InvenTreeRoleMixin, QRCodeView
from plugin.views import InvenTreePluginViewMixin

from .models import Company, ManufacturerPart, SupplierPart


class CompanyIndex(InvenTreeRoleMixin, ListView):
    """View for displaying list of companies."""

    model = Company
    template_name = 'company/index.html'
    context_object_name = 'companies'
    paginate_by = 50
    permission_required = 'company.view_company'

    def get_context_data(self, **kwargs):
        """Add extra context data to the company index page"""

        ctx = super().get_context_data(**kwargs)

        # Provide custom context data to the template,
        # based on the URL we use to access this page

        lookup = {
            reverse('supplier-index'): {
                'title': _('Suppliers'),
                'button_text': _('New Supplier'),
                'filters': {'is_supplier': 'true'},
                'pagetype': 'suppliers',
            },
            reverse('manufacturer-index'): {
                'title': _('Manufacturers'),
                'button_text': _('New Manufacturer'),
                'filters': {'is_manufacturer': 'true'},
                'pagetype': 'manufacturers',
            },
            reverse('customer-index'): {
                'title': _('Customers'),
                'button_text': _('New Customer'),
                'filters': {'is_customer': 'true'},
                'pagetype': 'customers',
            }
        }

        default = {
            'title': _('Companies'),
            'button_text': _('New Company'),
            'filters': {},
            'pagetype': 'companies'
        }

        context = None

        for item in lookup:
            if self.request.path == item:
                context = lookup[item]
                break

        if context is None:
            context = default

        for key, value in context.items():
            ctx[key] = value

        return ctx

    def get_queryset(self):
        """Retrieve the Company queryset based on HTTP request parameters.

        - supplier: Filter by supplier
        - customer: Filter by customer
        """
        queryset = Company.objects.all().order_by('name')

        if self.request.GET.get('supplier', None):
            queryset = queryset.filter(is_supplier=True)

        if self.request.GET.get('customer', None):
            queryset = queryset.filter(is_customer=True)

        return queryset


class CompanyDetail(InvenTreePluginViewMixin, DetailView):
    """Detail view for Company object."""
    context_obect_name = 'company'
    template_name = 'company/detail.html'
    queryset = Company.objects.all()
    model = Company
    permission_required = 'company.view_company'


class ManufacturerPartDetail(InvenTreePluginViewMixin, DetailView):
    """Detail view for ManufacturerPart."""
    model = ManufacturerPart
    template_name = 'company/manufacturer_part_detail.html'
    context_object_name = 'part'
    queryset = ManufacturerPart.objects.all()
    permission_required = 'purchase_order.view'


class SupplierPartDetail(InvenTreePluginViewMixin, DetailView):
    """Detail view for SupplierPart."""
    model = SupplierPart
    template_name = 'company/supplier_part_detail.html'
    context_object_name = 'part'
    queryset = SupplierPart.objects.all()
    permission_required = 'purchase_order.view'


class SupplierPartQRCode(QRCodeView):
    """View for displaying a QR code for a StockItem object."""

    ajax_form_title = _("Stock Item QR Code")
    role_required = 'stock.view'

    def get_qr_data(self):
        """Generate QR code data for the StockItem."""
        try:
            part = SupplierPart.objects.get(id=self.pk)
            return part.format_barcode()
        except SupplierPart.DoesNotExist:
            return None
