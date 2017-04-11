from django.shortcuts import render

from .models import Warehouse


def index(request):

    warehouses = Warehouse.objects.filter(parent=None)

    return render(request, 'stock/index.html', {'warehouses': warehouses})
