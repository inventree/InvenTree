from django.http import HttpResponse
from django.template import loader

from django.shortcuts import get_object_or_404, render

from .models import Supplier, SupplierPart

def index(request):
    """ The supplier index page simply displays all the suppliers
    """

    suppliers = Supplier.objects.order_by('name')

    return render(request, 'supplier/index.html', {'suppliers' : suppliers})


def detail(request, pk):
    """ The supplier detail page shown detailed information
    on a particular supplier
    """

    supplier = get_object_or_404(Supplier, pk=pk)

    return render(request, 'supplier/detail.html', {'supplier' : supplier})


def partDetail(request, pk):
    """ The supplier part-detail page shows detailed information
    on a particular supplier part
    """

    part = get_object_or_404(SupplierPart, pk=pk)

    return render(request, 'supplier/partdetail.html', {'part': part})