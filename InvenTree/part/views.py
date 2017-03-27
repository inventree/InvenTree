from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse

from .models import PartCategory, Part

def index(request):
    return HttpResponse("Hello world. This is the parts page")

def partDetail(request, part_id):
    
    part = get_object_or_404(Part, pk=part_id)
    
    return render(request, 'part/detail.html',
                  {'part': part})

def categoryList(request):
    categories = PartCategory.objects.filter(parent = None)
    
    return render(request, 'part/categorylist.html',
                  {'categories': categories
                  })

def category(request, category_id):
    
    # Find the category
    cat = get_object_or_404(PartCategory, pk=category_id)
    
    # Child categories
    childs = PartCategory.objects.filter(parent = cat.pk)
    
    return render(request, 'part/category.html',
                  {'category': cat,
                   'children': childs
                  })