from django.shortcuts import render
from InvenTree.views import QRCodeView
from InvenTree.views import InvenTreeRoleMixin
from .models import SalesOrderBasket
from django.views.generic import ListView, DetailView
from django.utils.translation import gettext_lazy as _
# Create your views here.

class SOBasketIndex(ListView):
    """ List view for all baskets """

    model = SalesOrderBasket
    template_name = 'baskets.html'
    context_object_name = 'baskets'

    def get_queryset(self):
        """ Retrieve the baskets,
        ensure that the most recent ones are returned first. """

        queryset = SalesOrderBasket.objects.all().order_by('-creation_date')

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx


class SOBasketDetail(DetailView):
    context_object_name = 'basket'
    queryset = SalesOrderBasket.objects.all().prefetch_related('sales_orders')
    template_name = 'basket_detail.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx

class BasketQRCode(QRCodeView):
    """ View for displaying a QR code for a basket object """

    ajax_form_title = _("Basket QR code")

    # role_required = ['stock_location.view', 'stock.view']

    def get_qr_data(self):
        """ Generate QR code data for the Basket """
        try:
            loc = SalesOrderBasket.objects.get(id=self.pk)
            return loc.format_barcode()
        except SalesOrderBasket.DoesNotExist:
            return None
