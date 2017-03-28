from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse, Http404

from rest_framework import generics

from .models import PartCategory, Part
from .serializers import PartSerializer, PartCategorySerializer

def index(request):
    return HttpResponse("Hello world. This is the parts page")

class PartDetail(generics.RetrieveAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer

class PartList(generics.ListAPIView):

    queryset = Part.objects.all()
    serializer_class = PartSerializer

class PartCategoryDetail(generics.RetrieveAPIView):
    
    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer
    
class PartCategoryList(generics.ListAPIView):

    queryset = PartCategory.objects.all()
    serializer_class = PartCategorySerializer