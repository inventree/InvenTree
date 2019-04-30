"""
Django views for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import get_object_or_404

from django.views.generic import DetailView, ListView
from django.forms import HiddenInput

from part.models import Part
from .models import Build, BuildItem
from .forms import EditBuildForm, EditBuildItemForm

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
            try:
                initials['part'] = Part.objects.get(pk=part_id)
            except Part.DoesNotExist:
                pass

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


class BuildItemCreate(AjaxCreateView):
    """ View for allocating a new part to a build """

    model = BuildItem
    form_class = EditBuildItemForm
    ajax_template_name = 'modal_form.html'
    ajax_form_title = 'Allocate new Part'

    def get_form(self):
        """ Create Form for making / editing new Part object """

        form = super(AjaxCreateView, self).get_form()

        # If the Build object is specified, hide the input field.
        # We do not want the users to be able to move a BuildItem to a different build
        if form['build'].value() is not None:
            form.fields['build'].widget = HiddenInput()

        # If the sub_part is supplied, limit to matching stock items
        part_id = self.get_param('part')

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                query = form.fields['stock_item'].queryset
                query = query.filter(part=part_id)
                form.fields['stock_item'].queryset = query
            except Part.DoesNotExist:
                pass

        return form

    def get_initial(self):
        """ Provide initial data for BomItem. Look for the folllowing in the GET data:

        - build: pk of the Build object
        """

        initials = super(AjaxCreateView, self).get_initial().copy()

        build_id = self.get_param('build')
        
        if build_id:
            try:
                initials['build'] = Build.objects.get(pk=build_id)
            except Build.DoesNotExist:
                pass

        return initials