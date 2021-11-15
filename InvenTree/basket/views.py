from django.shortcuts import render
from InvenTree.views import InvenTreeRoleMixin
from .models import SalesOrderBasket
from django.views.generic import ListView
# Create your views here.

class SOBasketIndex(ListView):
    """ List view for all purchase orders """

    model = SalesOrderBasket
    template_name = 'basket/baskets.html'
    context_object_name = 'baskets'

    def get_queryset(self):
        """ Retrieve the list of purchase orders,
        ensure that the most recent ones are returned first. """

        queryset = SalesOrderBasket.objects.all().order_by('-creation_date')

        return queryset

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        return ctx
