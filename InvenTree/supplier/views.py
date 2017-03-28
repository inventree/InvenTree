from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Supplier


def index(request):
    return HttpResponse("This is the suppliers page")


def supplierDetail(request, supplier_id):
    supplier = get_object_or_404(Supplier, pk=supplier_id)
    
    return render(request, 'supplier/detail.html',
                  {'supplier': supplier})
