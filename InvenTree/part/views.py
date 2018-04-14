
# Template stuff (WIP)
from django.http import HttpResponse
from django.template import loader

from InvenTree.models import FilterChildren
from .models import PartCategory, Part

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

def index(request):
    template = loader.get_template('part/index.html')

    parts = Part.objects.all()

    cat = None

    if 'category' in request.GET:
        cat_id = request.GET['category']

        cat = get_object_or_404(PartCategory, pk=cat_id)
        #cat = PartCategory.objects.get(pk=cat_id)
        parts = parts.filter(category = cat_id)

    context = {
        'parts' : parts.order_by('category__name'),
    }

    if cat:
        context['category'] = cat

    return HttpResponse(template.render(context, request))


def detail(request, pk):
    #template = loader.get_template('detail.html')

    part = get_object_or_404(Part, pk=pk)

    return render(request, 'part/detail.html', {'part' : part})

    #return HttpResponse("You're looking at part %s." % pk)


def bom(request, pk):
    part = get_object_or_404(Part, pk=pk)

    return render(request, 'part/bom.html', {'part': part})

def stock(request, pk):
    part = get_object_or_404(Part, pk=pk)

    return render(request, 'part/stock.html', {'part': part})

def track(request, pk):
    part = get_object_or_404(Part, pk=pk)

    return render(request, 'part/track.html', {'part': part})

