from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.urls import reverse

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .models import UniquePart, PartTrackingInfo


class TrackIndex(ListView):
    model = UniquePart
    template_name = 'track/index.html'
    context_object_name = 'parts'
    paginate_by = 50

    def get_queryset(self):
        return UniquePart.objects.order_by('part__name', 'serial')