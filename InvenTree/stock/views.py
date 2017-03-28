from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import Warehouse, StockItem


def index(request):
    
    warehouses = Warehouse.objects.filter(parent=None)
    
    return render(request, 'stock/index.html',
                  {'warehouses': warehouses
                  })
