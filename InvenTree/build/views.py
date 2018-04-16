# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404
from django.http import HttpResponseRedirect

from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView, DeleteView, CreateView

from .models import Build


class BuildIndex(ListView):
    model = Build
    template_name = 'build/index.html'
    context_object_name = 'builds'


class BuildDetail(DetailView):
    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'
