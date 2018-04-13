from django_filters.rest_framework import FilterSet, DjangoFilterBackend

# Template stuff (WIP)
from django.http import HttpResponse
from django.template import loader

from rest_framework import generics, permissions

from InvenTree.models import FilterChildren
from .models import PartCategory, Part

from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from .serializers import PartSerializer
from .serializers import PartCategorySerializer
#from .serializers import PartParameterSerializer
#from .serializers import PartTemplateSerializer

"""
class IndexView(generic.ListView):
    template_name = 'index.html'
    context_object_name = 'parts'

    def get_queryset(self):
        "Return the last five published questions."
        return Part.objects.all()

"""

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


#def results(request, question_id):
#    response = "You're looking at the results of question %s."
#    return HttpResponse(response % question_id)


class PartDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return detail on a single Part

    post:
    Update data for a single Part

    delete:
    Remove a part from the database

    """
    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


"""
class PartParamFilter(FilterSet):

    class Meta:
        model = PartParameter
        fields = ['part']

class PartParamList(generics.ListCreateAPIView):
    "

    get:
    Return a list of all part parameters (with optional filters)

    post:
    Create a new part parameter
    ""

    queryset = PartParameter.objects.all()
    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = PartParamFilter


class PartParamDetail(generics.RetrieveUpdateDestroyAPIView):
    ""

    get:
    Detail view of a single PartParameter

    post:
    Update data for a PartParameter

    delete:
    Remove a PartParameter from the database

    "

    queryset = PartParameter.objects.all()
    serializer_class = PartParameterSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
"""

class PartFilter(FilterSet):

    class Meta:
        model = Part
        fields = ['category']


class PartList(generics.ListCreateAPIView):
    """

    get:
    List of Parts, with optional filters

    post:
    Create a new Part
    """

    queryset = Part.objects.all()
    serializer_class = PartSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filter_class = PartFilter


class PartCategoryDetail(generics.RetrieveUpdateDestroyAPIView):
    """

    get:
    Return information on a single PartCategory

    post:
    Update a PartCategory

    delete:
    Remove a PartCategory

    """
    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartCategoryList(generics.ListCreateAPIView):
    """

    get:
    Return a list of all categories
    (with optional filters)

    post:
    Create a new PartCategory
    """

    def get_queryset(self):
        params = self.request.query_params

        categories = PartCategory.objects.all()

        categories = FilterChildren(categories, params.get('parent', None))

        return categories

    queryset = PartCategory.objects.filter(parent=None)
    serializer_class = PartCategorySerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


"""
class PartTemplateDetail(generics.RetrieveUpdateDestroyAPIView):
    ""

    get:
    Return detail on a single PartParameterTemplate object

    post:
    Update a PartParameterTemplate object

    delete:
    Remove a PartParameterTemplate object

    ""

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)


class PartTemplateList(generics.ListCreateAPIView):
    ""

    get:
    Return a list of all PartParameterTemplate objects
    (with optional query filters)

    post:
    Create a new PartParameterTemplate object

    ""

    queryset = PartParameterTemplate.objects.all()
    serializer_class = PartTemplateSerializer
    permission_classes = (permissions.IsAuthenticatedOrReadOnly,)

"""
