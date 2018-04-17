# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from part.models import Part
from .models import Build

from .forms import EditBuildForm

class BuildIndex(ListView):
    model = Build
    template_name = 'build/index.html'
    context_object_name = 'builds'

    def get_queryset(self):
        return Build.objects.order_by('status', '-completion_date')

    def get_context_data(self, **kwargs):

        context = super(BuildIndex, self).get_context_data(**kwargs).copy()

        context['active'] = self.get_queryset().filter(status__in=[Build.PENDING, Build.HOLDING])

        context['complete'] = self.get_queryset().filter(status=Build.COMPLETE)
        context['cancelled'] = self.get_queryset().filter(status=Build.CANCELLED)

        return context


class BuildDetail(DetailView):
    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'


class BuildCreate(CreateView):
    model = Build
    template_name = 'build/create.html'
    context_object_name = 'build'
    form_class = EditBuildForm

    def get_initial(self):
        initials = super(BuildCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)

        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)

        return initials


class BuildUpdate(UpdateView):
    model = Build
    form_class = EditBuildForm
    context_object_name = 'build'
    template_name = 'build/update.html'
