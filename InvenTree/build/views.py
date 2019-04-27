"""
Django views for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

from django.views.generic import DetailView, ListView

from part.models import Part
from .models import Build
from .forms import EditBuildForm

from InvenTree.views import AjaxView, AjaxUpdateView, AjaxCreateView


class BuildIndex(ListView):
    """ View for displaying list of Builds
    """
    model = Build
    template_name = 'build/index.html'
    context_object_name = 'builds'

    def get_queryset(self):
        """ Return all Build objects (order by date, newest first) """
        return Build.objects.order_by('status', '-completion_date')

    def get_context_data(self, **kwargs):

        context = super(BuildIndex, self).get_context_data(**kwargs).copy()

        """
        context['active'] = self.get_queryset().filter(status__in=[Build.PENDING, Build.HOLDING])

        context['complete'] = self.get_queryset().filter(status=Build.COMPLETE)
        context['cancelled'] = self.get_queryset().filter(status=Build.CANCELLED)
        """

        return context


class BuildCancel(AjaxView):
    """ View to cancel a Build.
    Provides a cancellation information dialog
    """
    model = Build
    template_name = 'build/cancel.html'
    ajax_form_title = 'Cancel Build'
    context_object_name = 'build'
    fields = []

    def post(self, request, *args, **kwargs):
        """ Handle POST request. Mark the build status as CANCELLED """

        build = get_object_or_404(Build, pk=self.kwargs['pk'])

        build.status = Build.CANCELLED
        build.save()

        return self.renderJsonResponse(request, None)

    def get_data(self):
        """ Provide JSON context data. """
        return {
            'info': 'Build was cancelled'
        }


class BuildDetail(DetailView):
    """ Detail view of a single Build object. """
    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'


class BuildAllocate(DetailView):
    """ View for allocating parts to a Build """
    model = Build
    context_object_name = 'build'
    template_name = 'build/allocate.html'


class BuildCreate(AjaxCreateView):
    """ View to create a new Build object """
    model = Build
    context_object_name = 'build'
    form_class = EditBuildForm
    ajax_form_title = 'Start new Build'
    ajax_template_name = 'modal_form.html'

    def get_initial(self):
        """ Get initial parameters for Build creation.

        If 'part' is specified in the GET query, initialize the Build with the specified Part
        """

        initials = super(BuildCreate, self).get_initial().copy()

        part_id = self.request.GET.get('part', None)

        if part_id:
            initials['part'] = get_object_or_404(Part, pk=part_id)

        return initials

    def get_data(self):
        return {
            'success': 'Created new build',
        }


class BuildUpdate(AjaxUpdateView):
    """ View for editing a Build object """
    
    model = Build
    form_class = EditBuildForm
    context_object_name = 'build'
    ajax_form_title = 'Edit Build Details'
    ajax_template_name = 'modal_form.html'

    def get_data(self):
        return {
            'info': 'Edited build',
        }
