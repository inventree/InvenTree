from django.http import HttpResponse
from django.template import loader

from django.shortcuts import get_object_or_404, render

from .models import StockItem, StockLocation

def index(request):
    template = loader.get_template('stock/index.html')

    items = StockItem.objects.all()

    location = None

    if 'location' in request.GET:
        loc_id = request.GET['location']

        location = get_object_or_404(StockLocation, pk=loc_id)

        items = items.filter(location = loc_id)

        children = StockLocation.objects.filter(parent = loc_id)

    else:
        # No stock items can exist without a location
        items = None
        location = None
        children = StockLocation.objects.filter(parent__isnull=True)

    context = {
        'items' : items,
        'location' : location,
        'children' : children,
    }

    return HttpResponse(template.render(context, request))


def detail(request, pk):

    item = get_object_or_404(Stock, pk=pk)

    return render(request, 'stock/detail.html', {'item' : item})