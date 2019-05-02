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
from .forms import EditBuildForm, EditBuildItemForm, CompleteBuildForm
from stock.models import StockLocation, StockItem

from InvenTree.views import AjaxView, AjaxUpdateView, AjaxCreateView, AjaxDeleteView


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

        context['active'] = self.get_queryset().filter(status__in=[Build.PENDING, ])

        context['completed'] = self.get_queryset().filter(status=Build.COMPLETE)
        context['cancelled'] = self.get_queryset().filter(status=Build.CANCELLED)

        return context


class BuildCancel(AjaxView):
    """ View to cancel a Build.
    Provides a cancellation information dialog
    """
    model = Build
    ajax_template_name = 'build/cancel.html'
    ajax_form_title = 'Cancel Build'
    context_object_name = 'build'
    fields = []

    def post(self, request, *args, **kwargs):
        """ Handle POST request. Mark the build status as CANCELLED """

        build = get_object_or_404(Build, pk=self.kwargs['pk'])

        build.cancelBuild(request.user)

        return self.renderJsonResponse(request, None)

    def get_data(self):
        """ Provide JSON context data. """
        return {
            'danger': 'Build was cancelled'
        }


class BuildComplete(AjaxUpdateView):
    """ View to mark a build as Complete.

    - Notifies the user of which parts will be removed from stock.
    - Removes allocated items from stock
    - Deletes pending BuildItem objects
    """

    model = Build
    form_class = CompleteBuildForm
    context_object_name = "build"
    ajax_form_title = "Complete Build"
    ajax_template_name = "build/complete.html"

    def get_initial(self):
        """ Get initial form data for the CompleteBuild form

        - If the part being built has a default location, pre-select that location
        """
        
        initials = super(BuildComplete, self).get_initial().copy()

        build = self.get_object()
        if build.part.default_location is not None:
            try:
                location = StockLocation.objects.get(pk=build.part.default_location.id)
                initials['location'] = location
            except StockLocation.DoesNotExist:
                pass

        return initials

    def get_context_data(self, **kwargs):
        """ Get context data for passing to the rendered form

        - Build information is required
        """

        build = self.get_object()

        # Build object
        context = super(BuildComplete, self).get_context_data(**kwargs).copy()
        context['build'] = build

        # Items to be removed from stock
        taking = BuildItem.objects.filter(build=build.id)
        context['taking'] = taking

        return context
    
    def post(self, request, *args, **kwargs):
        """ Handle POST request. Mark the build as COMPLETE
        
        - If the form validation passes, the Build objects completeBuild() method is called
        - Otherwise, the form is passed back to the client
        """

        build = self.get_object()

        form = self.get_form()

        confirm = request.POST.get('confirm', False)

        loc_id = request.POST.get('location', None)

        valid = False

        if confirm is False:
            form.errors['confirm'] = [
                'Confirm completion of build',
            ]
        else:
            try:
                location = StockLocation.objects.get(id=loc_id)
                valid = True
            except StockLocation.DoesNotExist:
                print('id:', loc_id)
                form.errors['location'] = ['Invalid location selected']

            if valid:
                build.completeBuild(location, request.user)

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)

    def get_data(self):
        """ Provide feedback data back to the form """
        return {
            'info': 'Build marked as COMPLETE'
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

    def get_context_data(self, **kwargs):
        """ Provide extra context information for the Build allocation page """

        context = super(DetailView, self).get_context_data(**kwargs)

        build = self.get_object()
        part = build.part
        bom_items = part.bom_items

        context['part'] = part
        context['bom_items'] = bom_items

        return context


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


class BuildItemDelete(AjaxDeleteView):
    """ View to 'unallocate' a BuildItem.
    Really we are deleting the BuildItem object from the database.
    """

    model = BuildItem
    ajax_template_name = 'build/delete_build_item.html'
    ajax_form_title = 'Unallocate Stock'
    context_object_name = 'item'

    def get_data(self):
        return {
            'danger': 'Removed parts from build allocation'
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
        build_id = form['build'].value()

        if build_id is not None:
            form.fields['build'].widget = HiddenInput()

        # If the sub_part is supplied, limit to matching stock items
        part_id = self.get_param('part')

        if part_id:
            try:
                Part.objects.get(pk=part_id)

                query = form.fields['stock_item'].queryset
                
                # Only allow StockItem objects which match the current part
                query = query.filter(part=part_id)

                if build_id is not None:
                    # Exclude StockItem objects which are already allocated to this build and part
                    query = query.exclude(id__in=[item.stock_item.id for item in BuildItem.objects.filter(build=build_id, stock_item__part=part_id)])

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


class BuildItemEdit(AjaxUpdateView):
    """ View to edit a BuildItem object """

    model = BuildItem
    ajax_template_name = 'modal_form.html'
    form_class = EditBuildItemForm
    ajax_form_title = 'Edit Stock Allocation'

    def get_data(self):
        return {
            'info': 'Updated Build Item',
        }

    def get_form(self):
        """ Create form for editing a BuildItem.

        - Limit the StockItem options to items that match the part
        """

        build_item = self.get_object()

        form = super(BuildItemEdit, self).get_form()

        query = StockItem.objects.all()
        
        if build_item.stock_item:
            part_id = build_item.stock_item.part.id
            query = query.filter(part=part_id)

        form.fields['stock_item'].queryset = query

        form.fields['build'].widget = HiddenInput()

        return form
