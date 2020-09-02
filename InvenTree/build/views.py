"""
Django views for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.views.generic import DetailView, ListView, UpdateView
from django.forms import HiddenInput
from django.urls import reverse

from part.models import Part
from .models import Build, BuildItem
from . import forms
from stock.models import StockLocation, StockItem

from InvenTree.views import AjaxUpdateView, AjaxCreateView, AjaxDeleteView
from InvenTree.helpers import str2bool, ExtractSerialNumbers
from InvenTree.status_codes import BuildStatus


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

        context['BuildStatus'] = BuildStatus

        context['active'] = self.get_queryset().filter(status__in=BuildStatus.ACTIVE_CODES)

        context['completed'] = self.get_queryset().filter(status=BuildStatus.COMPLETE)
        context['cancelled'] = self.get_queryset().filter(status=BuildStatus.CANCELLED)

        return context


class BuildCancel(AjaxUpdateView):
    """ View to cancel a Build.
    Provides a cancellation information dialog
    """

    model = Build
    ajax_template_name = 'build/cancel.html'
    ajax_form_title = _('Cancel Build')
    context_object_name = 'build'
    form_class = forms.CancelBuildForm

    def post(self, request, *args, **kwargs):
        """ Handle POST request. Mark the build status as CANCELLED """

        build = self.get_object()

        form = self.get_form()

        valid = form.is_valid()

        confirm = str2bool(request.POST.get('confirm_cancel', False))

        if confirm:
            build.cancelBuild(request.user)
        else:
            form.errors['confirm_cancel'] = [_('Confirm build cancellation')]
            valid = False

        data = {
            'form_valid': valid,
            'danger': _('Build was cancelled')
        }

        return self.renderJsonResponse(request, form, data=data)


class BuildAutoAllocate(AjaxUpdateView):
    """ View to auto-allocate parts for a build.
    Follows a simple set of rules to automatically allocate StockItem objects.

    Ref: build.models.Build.getAutoAllocations()
    """

    model = Build
    form_class = forms.ConfirmBuildForm
    context_object_name = 'build'
    ajax_form_title = _('Allocate Stock')
    ajax_template_name = 'build/auto_allocate.html'

    def get_context_data(self, *args, **kwargs):
        """ Get the context data for form rendering. """

        context = {}

        try:
            build = Build.objects.get(id=self.kwargs['pk'])
            context['build'] = build
            context['allocations'] = build.getAutoAllocations()
        except Build.DoesNotExist:
            context['error'] = _('No matching build found')

        return context

    def post(self, request, *args, **kwargs):
        """ Handle POST request. Perform auto allocations.

        - If the form validation passes, perform allocations
        - Otherwise, the form is passed back to the client
        """

        build = self.get_object()
        form = self.get_form()

        confirm = request.POST.get('confirm', False)

        valid = False

        if confirm is False:
            form.errors['confirm'] = [_('Confirm stock allocation')]
            form.non_field_errors = [_('Check the confirmation box at the bottom of the list')]
        else:
            build.autoAllocate()
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data, context=self.get_context_data())


class BuildUnallocate(AjaxUpdateView):
    """ View to un-allocate all parts from a build.

    Provides a simple confirmation dialog with a BooleanField checkbox.
    """

    model = Build
    form_class = forms.ConfirmBuildForm
    ajax_form_title = _("Unallocate Stock")
    ajax_template_name = "build/unallocate.html"

    def post(self, request, *args, **kwargs):

        build = self.get_object()
        form = self.get_form()
        
        confirm = request.POST.get('confirm', False)

        valid = False

        if confirm is False:
            form.errors['confirm'] = [_('Confirm unallocation of build stock')]
            form.non_field_errors = [_('Check the confirmation box')]
        else:
            build.unallocateStock()
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)


class BuildComplete(AjaxUpdateView):
    """ View to mark a build as Complete.

    - Notifies the user of which parts will be removed from stock.
    - Removes allocated items from stock
    - Deletes pending BuildItem objects
    """

    model = Build
    form_class = forms.CompleteBuildForm
    context_object_name = "build"
    ajax_form_title = _("Complete Build")
    ajax_template_name = "build/complete.html"

    def get_form(self):
        """ Get the form object.

        If the part is trackable, include a field for serial numbers.
        """
        build = self.get_object()

        form = super().get_form()

        if not build.part.trackable:
            form.fields.pop('serial_numbers')
        else:

            form.field_placeholder['serial_numbers'] = build.part.getSerialNumberString(build.quantity)

            form.rebuild_layout()

        return form

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

        build = Build.objects.get(id=self.kwargs['pk'])

        context = {}

        # Build object
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

        confirm = str2bool(request.POST.get('confirm', False))

        loc_id = request.POST.get('location', None)

        valid = False

        if confirm is False:
            form.errors['confirm'] = [
                _('Confirm completion of build'),
            ]
        else:
            try:
                location = StockLocation.objects.get(id=loc_id)
                valid = True
            except (ValueError, StockLocation.DoesNotExist):
                form.errors['location'] = [_('Invalid location selected')]

            serials = []

            if build.part.trackable:
                # A build for a trackable part may optionally specify serial numbers.

                sn = request.POST.get('serial_numbers', '')

                sn = str(sn).strip()

                # If the user has specified serial numbers, check they are valid
                if len(sn) > 0:
                    try:
                        # Exctract a list of provided serial numbers
                        serials = ExtractSerialNumbers(sn, build.quantity)

                        existing = []

                        for serial in serials:
                            if build.part.checkIfSerialNumberExists(serial):
                                existing.append(serial)

                        if len(existing) > 0:
                            exists = ",".join([str(x) for x in existing])
                            form.errors['serial_numbers'] = [_('The following serial numbers already exist: ({sn})'.format(sn=exists))]
                            valid = False

                    except ValidationError as e:
                        form.errors['serial_numbers'] = e.messages
                        valid = False

            if valid:
                if not build.completeBuild(location, serials, request.user):
                    form.non_field_errors = [('Build could not be completed')]
                    valid = False

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data, context=self.get_context_data())

    def get_data(self):
        """ Provide feedback data back to the form """
        return {
            'info': _('Build marked as COMPLETE')
        }


class BuildNotes(UpdateView):
    """ View for editing the 'notes' field of a Build object.
    """

    context_object_name = 'build'
    template_name = 'build/notes.html'
    model = Build

    fields = ['notes']

    def get_success_url(self):
        return reverse('build-notes', kwargs={'pk': self.get_object().id})

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)
        
        ctx['editing'] = str2bool(self.request.GET.get('edit', ''))

        return ctx


class BuildDetail(DetailView):
    """ Detail view of a single Build object. """
    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'

    def get_context_data(self, **kwargs):

        ctx = super(DetailView, self).get_context_data(**kwargs)

        build = self.get_object()

        ctx['bom_price'] = build.part.get_price_info(build.quantity, buy=False)
        ctx['BuildStatus'] = BuildStatus

        return ctx


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
        context['BuildStatus'] = BuildStatus

        context['bom_price'] = build.part.get_price_info(build.quantity, buy=False)

        if str2bool(self.request.GET.get('edit', None)):
            context['editing'] = True

        return context


class BuildCreate(AjaxCreateView):
    """ View to create a new Build object """
    model = Build
    context_object_name = 'build'
    form_class = forms.EditBuildForm
    ajax_form_title = _('Start new Build')
    ajax_template_name = 'modal_form.html'

    def get_initial(self):
        """ Get initial parameters for Build creation.

        If 'part' is specified in the GET query, initialize the Build with the specified Part
        """

        initials = super(BuildCreate, self).get_initial().copy()

        # User has provided a Part ID
        initials['part'] = self.request.GET.get('part', None)

        initials['parent'] = self.request.GET.get('parent', None)

        # User has provided a SalesOrder ID
        initials['sales_order'] = self.request.GET.get('sales_order', None)

        initials['quantity'] = self.request.GET.get('quantity', 1)

        return initials

    def get_data(self):
        return {
            'success': _('Created new build'),
        }


class BuildUpdate(AjaxUpdateView):
    """ View for editing a Build object """
    
    model = Build
    form_class = forms.EditBuildForm
    context_object_name = 'build'
    ajax_form_title = _('Edit Build Details')
    ajax_template_name = 'modal_form.html'

    def get_data(self):
        return {
            'info': _('Edited build'),
        }


class BuildDelete(AjaxDeleteView):
    """ View to delete a build """

    model = Build
    ajax_template_name = 'build/delete_build.html'
    ajax_form_title = _('Delete Build')


class BuildItemDelete(AjaxDeleteView):
    """ View to 'unallocate' a BuildItem.
    Really we are deleting the BuildItem object from the database.
    """

    model = BuildItem
    ajax_template_name = 'build/delete_build_item.html'
    ajax_form_title = _('Unallocate Stock')
    context_object_name = 'item'

    def get_data(self):
        return {
            'danger': _('Removed parts from build allocation')
        }


class BuildItemCreate(AjaxCreateView):
    """ View for allocating a new part to a build """

    model = BuildItem
    form_class = forms.EditBuildItemForm
    ajax_template_name = 'build/create_build_item.html'
    ajax_form_title = _('Allocate new Part')

    part = None
    available_stock = None

    def get_context_data(self):
        ctx = super(AjaxCreateView, self).get_context_data()

        if self.part:
            ctx['part'] = self.part

        if self.available_stock:
            ctx['stock'] = self.available_stock
        else:
            ctx['no_stock'] = True

        return ctx

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
                self.part = Part.objects.get(pk=part_id)

                query = form.fields['stock_item'].queryset
                
                # Only allow StockItem objects which match the current part
                query = query.filter(part=part_id)

                if build_id is not None:
                    try:
                        build = Build.objects.get(id=build_id)
                        
                        if build.take_from is not None:
                            # Limit query to stock items that are downstream of the 'take_from' location
                            query = query.filter(location__in=[loc for loc in build.take_from.getUniqueChildren()])
                            
                    except Build.DoesNotExist:
                        pass

                    # Exclude StockItem objects which are already allocated to this build and part
                    query = query.exclude(id__in=[item.stock_item.id for item in BuildItem.objects.filter(build=build_id, stock_item__part=part_id)])

                form.fields['stock_item'].queryset = query

                stocks = query.all()
                self.available_stock = stocks

                # If there is only one item selected, select it
                if len(stocks) == 1:
                    form.fields['stock_item'].initial = stocks[0].id
                # There is no stock available
                elif len(stocks) == 0:
                    # TODO - Add a message to the form describing the problem
                    pass

            except Part.DoesNotExist:
                self.part = None
                pass

        return form

    def get_initial(self):
        """ Provide initial data for BomItem. Look for the folllowing in the GET data:

        - build: pk of the Build object
        """

        initials = super(AjaxCreateView, self).get_initial().copy()

        build_id = self.get_param('build')
        part_id = self.get_param('part')

        # Reference to a Part object
        part = None

        # Reference to a StockItem object
        item = None
        
        # Reference to a Build object
        build = None

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                initials['part'] = part
            except Part.DoesNotExist:
                pass

        if build_id:
            try:
                build = Build.objects.get(pk=build_id)
                initials['build'] = build
            except Build.DoesNotExist:
                pass

        quantity = self.request.GET.get('quantity', None)

        if quantity is not None:
            quantity = float(quantity)

        if quantity is None:
            # Work out how many parts remain to be alloacted for the build
            if part:
                quantity = build.getUnallocatedQuantity(part)
                
        item_id = self.get_param('item')

        # If the request specifies a particular StockItem
        if item_id:
            try:
                item = StockItem.objects.get(pk=item_id)
            except:
                pass

        # If a StockItem is not selected, try to auto-select one
        if item is None and part is not None:
            items = StockItem.objects.filter(part=part)
            if items.count() == 1:
                item = items.first()

        # Finally, if a StockItem is selected, ensure the quantity is not too much
        if item is not None:
            if quantity is None:
                quantity = item.unallocated_quantity()
            else:
                quantity = min(quantity, item.unallocated_quantity())

        if quantity is not None:
            initials['quantity'] = quantity

        return initials


class BuildItemEdit(AjaxUpdateView):
    """ View to edit a BuildItem object """

    model = BuildItem
    ajax_template_name = 'modal_form.html'
    form_class = forms.EditBuildItemForm
    ajax_form_title = _('Edit Stock Allocation')

    def get_data(self):
        return {
            'info': _('Updated Build Item'),
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
