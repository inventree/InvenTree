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
from .models import Build, BuildItem, BuildOrderAttachment
from . import forms
from stock.models import StockLocation, StockItem

from InvenTree.views import AjaxUpdateView, AjaxCreateView, AjaxDeleteView
from InvenTree.views import InvenTreeRoleMixin
from InvenTree.helpers import str2bool, extract_serial_numbers, normalize
from InvenTree.status_codes import BuildStatus


class BuildIndex(InvenTreeRoleMixin, ListView):
    """ View for displaying list of Builds
    """
    model = Build
    template_name = 'build/index.html'
    context_object_name = 'builds'
    role_required = 'build.view'

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
    role_required = 'build.change'

    def validate(self, build, form, **kwargs):

        confirm = str2bool(form.cleaned_data.get('confirm_cancel', False))

        if not confirm:
            form.add_error('confirm_cancel', _('Confirm build cancellation'))

    def save(self, build, form, **kwargs):
        """
        Cancel the build.
        """

        build.cancelBuild(self.request.user)

    def get_data(self):
        return {
            'danger': _('Build was cancelled')
        }


class BuildAutoAllocate(AjaxUpdateView):
    """ View to auto-allocate parts for a build.
    Follows a simple set of rules to automatically allocate StockItem objects.

    Ref: build.models.Build.getAutoAllocations()
    """

    model = Build
    form_class = forms.AutoAllocateForm
    context_object_name = 'build'
    ajax_form_title = _('Allocate Stock')
    ajax_template_name = 'build/auto_allocate.html'
    role_required = 'build.change'

    def get_initial(self):
        """
        Initial values for the form.
        """

        initials = super().get_initial()

        # Pointing to a particular build output?
        output = self.get_param('output')

        if output:
            try:
                output = StockItem.objects.get(pk=output)
                initials['output'] = output
            except (ValueError, StockItem.DoesNotExist):
                pass

        return initials

    def get_context_data(self, *args, **kwargs):
        """
        Get the context data for form rendering.
        """

        context = {}

        build = self.get_object()

        form = self.get_form()

        output_id = form['output'].value()

        try:
            output = StockItem.objects.get(pk=output_id)
        except (ValueError, StockItem.DoesNotExist):
            output = None

        if output:
            context['output'] = output
            context['allocations'] = build.getAutoAllocations(output)

        context['build'] = build

        return context

    def get_form(self):

        form = super().get_form()

        if form['output'].value():
            # Hide the 'output' field
            form.fields['output'].widget = HiddenInput()

        return form

    def validate(self, build, form, **kwargs):

        output = form.cleaned_data.get('output', None)

        if not output:
            form.add_error(None, _('Build output must be specified'))

    def save(self, build, form, **kwargs):
        """
        Once the form has been validated,
        perform auto-allocations
        """

        output = form.cleaned_data.get('output', None)

        build.autoAllocate(output)

    def get_data(self):
        return {
            'success': _('Allocated stock to build output'),
        }


class BuildOutputCreate(AjaxUpdateView):
    """
    Create a new build output (StockItem) for a given build.
    """

    model = Build
    form_class = forms.BuildOutputCreateForm
    ajax_template_name = 'build/build_output_create.html'
    ajax_form_title = _('Create Build Output')
    role_required = 'build.change'

    def validate(self, build, form, **kwargs):
        """
        Validation for the form:
        """

        quantity = form.cleaned_data.get('output_quantity', None)
        serials = form.cleaned_data.get('serial_numbers', None)

        # Check that the serial numbers are valid
        if serials:
            try:
                extracted = extract_serial_numbers(serials, quantity)

                if extracted:
                    # Check for conflicting serial numbers
                    conflicts = build.part.find_conflicting_serial_numbers(extracted)

                    if len(conflicts) > 0:
                        msg = ",".join([str(c) for c in conflicts])
                        form.add_error(
                            'serial_numbers',
                            _('Serial numbers already exist') + ': ' + msg,
                        )

            except ValidationError as e:
                form.add_error('serial_numbers', e.messages)

        else:
            # If no serial numbers are provided, should they be?
            if build.part.trackable:
                form.add_error('serial_numbers', _('Serial numbers required for trackable build output'))

    def save(self, build, form, **kwargs):
        """
        Create a new build output
        """

        data = form.cleaned_data

        quantity = data.get('output_quantity', None)
        batch = data.get('batch', None)

        serials = data.get('serial_numbers', None)

        if serials:
            serial_numbers = extract_serial_numbers(serials, quantity)
        else:
            serial_numbers = None

        build.create_build_output(
            quantity,
            serials=serial_numbers,
            batch=batch,
        )

    def get_initial(self):

        initials = super().get_initial()

        build = self.get_object()

        # Calculate the required quantity
        quantity = max(0, build.remaining - build.incomplete_count)
        initials['quantity'] = quantity

        return initials

    def get_form(self):

        build = self.get_object()
        part = build.part

        context = self.get_form_kwargs()

        # Pass the 'part' through to the form,
        # so we can add the next serial number as a placeholder
        context['build'] = build

        form = self.form_class(**context)

        # If the part is not trackable, hide the serial number input
        if not part.trackable:
            form.fields['serial_numbers'].widget = HiddenInput()

        return form


class BuildOutputDelete(AjaxUpdateView):
    """
    Delete a build output (StockItem) for a given build.

    Form is a simple confirmation dialog
    """

    model = Build
    form_class = forms.BuildOutputDeleteForm
    ajax_form_title = _('Delete Build Output')
    role_required = 'build.delete'

    def get_initial(self):

        initials = super().get_initial()

        output = self.get_param('output')

        initials['output_id'] = output

        return initials

    def validate(self, build, form, **kwargs):

        data = form.cleaned_data

        confirm = data.get('confirm', False)

        if not confirm:
            form.add_error('confirm', _('Confirm unallocation of build stock'))
            form.add_error(None, _('Check the confirmation box'))

        output_id = data.get('output_id', None)
        output = None

        try:
            output = StockItem.objects.get(pk=output_id)
        except (ValueError, StockItem.DoesNotExist):
            pass

        if output:
            if not output.build == build:
                form.add_error(None, _('Build output does not match build'))
        else:
            form.add_error(None, _('Build output must be specified'))

    def save(self, build, form, **kwargs):

        output_id = form.cleaned_data.get('output_id')

        output = StockItem.objects.get(pk=output_id)

        build.deleteBuildOutput(output)

    def get_data(self):
        return {
            'danger': _('Build output deleted'),
        }


class BuildUnallocate(AjaxUpdateView):
    """ View to un-allocate all parts from a build.

    Provides a simple confirmation dialog with a BooleanField checkbox.
    """

    model = Build
    form_class = forms.UnallocateBuildForm
    ajax_form_title = _("Unallocate Stock")
    ajax_template_name = "build/unallocate.html"
    role_required = 'build.change'

    def get_initial(self):

        initials = super().get_initial()

        # Pointing to a particular build output?
        output = self.get_param('output')

        if output:
            initials['output_id'] = output

        # Pointing to a particular part?
        part = self.get_param('part')

        if part:
            initials['part_id'] = part

        return initials

    def post(self, request, *args, **kwargs):

        build = self.get_object()
        form = self.get_form()
        
        confirm = request.POST.get('confirm', False)

        output_id = request.POST.get('output_id', None)

        try:
            output = StockItem.objects.get(pk=output_id)
        except (ValueError, StockItem.DoesNotExist):
            output = None

        part_id = request.POST.get('part_id', None)

        try:
            part = Part.objects.get(pk=part_id)
        except (ValueError, Part.DoesNotExist):
            part = None

        valid = False

        if confirm is False:
            form.add_error('confirm', _('Confirm unallocation of build stock'))
            form.add_error(None, _('Check the confirmation box'))
        else:
            build.unallocateStock(output=output, part=part)
            valid = True

        data = {
            'form_valid': valid,
        }

        return self.renderJsonResponse(request, form, data)


class BuildComplete(AjaxUpdateView):
    """
    View to mark the build as complete.

    Requirements:
    - There can be no outstanding build outputs
    - The "completed" value must meet or exceed the "quantity" value
    """

    model = Build
    form_class = forms.CompleteBuildForm
    role_required = 'build.change'
    ajax_form_title = _('Complete Build Order')
    ajax_template_name = 'build/complete.html'

    def validate(self, build, form, **kwargs):

        if not build.can_complete:
            form.add_error(None, _('Build order cannot be completed'))

    def save(self, build, form, **kwargs):
        """
        Perform the build completion step
        """

        build.complete_build(self.request.user)

    def get_data(self):
        return {
            'success': _('Completed build order')
        }


class BuildOutputComplete(AjaxUpdateView):
    """
    View to mark a particular build output as Complete.

    - Notifies the user of which parts will be removed from stock.
    - Removes allocated items from stock
    - Deletes pending BuildItem objects
    """

    model = Build
    form_class = forms.CompleteBuildOutputForm
    context_object_name = "build"
    ajax_form_title = _("Complete Build Output")
    ajax_template_name = "build/complete_output.html"
    role_required = 'build.change'

    def get_form(self):
        
        build = self.get_object()

        form = super().get_form()

        # Extract the build output object
        output = None
        output_id = form['output'].value()

        try:
            output = StockItem.objects.get(pk=output_id)
        except (ValueError, StockItem.DoesNotExist):
            pass

        if output:
            if build.isFullyAllocated(output):
                form.fields['confirm_incomplete'].widget = HiddenInput()

        return form

    def validate(self, build, form, **kwargs):

        data = form.cleaned_data

        output = data.get('output', None)

        if output:

            quantity = data.get('quantity', None)

            if quantity and quantity > output.quantity:
                form.add_error('quantity', _('Quantity to complete cannot exceed build output quantity'))

            if not build.isFullyAllocated(output):
                confirm = str2bool(data.get('confirm_incomplete', False))

                if not confirm:
                    form.add_error('confirm_incomplete', _('Confirm completion of incomplete build'))

        else:
            form.add_error(None, _('Build output must be specified'))

    def get_initial(self):
        """ Get initial form data for the CompleteBuild form

        - If the part being built has a default location, pre-select that location
        """
        
        initials = super().get_initial()
        build = self.get_object()

        if build.part.default_location is not None:
            try:
                location = StockLocation.objects.get(pk=build.part.default_location.id)
                initials['location'] = location
            except StockLocation.DoesNotExist:
                pass

        output = self.get_param('output', None)

        if output:
            try:
                output = StockItem.objects.get(pk=output)
            except (ValueError, StockItem.DoesNotExist):
                output = None

        # Output has not been supplied? Try to "guess"
        if not output:

            incomplete = build.get_build_outputs(complete=False)

            if incomplete.count() == 1:
                output = incomplete[0]

        if output is not None:
            initials['output'] = output

        initials['location'] = build.destination

        return initials

    def get_context_data(self, **kwargs):
        """
        Get context data for passing to the rendered form

        - Build information is required
        """

        build = self.get_object()

        context = {}

        # Build object
        context['build'] = build

        form = self.get_form()

        output = form['output'].value()

        if output:
            try:
                output = StockItem.objects.get(pk=output)
                context['output'] = output
                context['fully_allocated'] = build.isFullyAllocated(output)
                context['allocated_parts'] = build.allocatedParts(output)
                context['unallocated_parts'] = build.unallocatedParts(output)
            except (ValueError, StockItem.DoesNotExist):
                pass

        return context

    def save(self, build, form, **kwargs):

        data = form.cleaned_data

        location = data.get('location', None)
        output = data.get('output', None)

        # Complete the build output
        build.completeBuildOutput(
            output,
            self.request.user,
            location=location,
        )
    
    def get_data(self):
        """ Provide feedback data back to the form """
        return {
            'success': _('Build output completed')
        }


class BuildNotes(UpdateView):
    """ View for editing the 'notes' field of a Build object.
    """

    context_object_name = 'build'
    template_name = 'build/notes.html'
    model = Build
    role_required = 'build.view'

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
    role_required = 'build.view'

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
    role_required = ['build.change']

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
    ajax_form_title = _('New Build Order')
    ajax_template_name = 'modal_form.html'
    role_required = 'build.add'

    def get_form(self):
        form = super().get_form()

        if form['part'].value():
            form.fields['part'].widget = HiddenInput()

        return form

    def get_initial(self):
        """ Get initial parameters for Build creation.

        If 'part' is specified in the GET query, initialize the Build with the specified Part
        """

        initials = super(BuildCreate, self).get_initial().copy()

        part = self.request.GET.get('part', None)

        if part:

            try:
                part = Part.objects.get(pk=part)
                # User has provided a Part ID
                initials['part'] = part
                initials['destination'] = part.get_default_location()
            except (ValueError, Part.DoesNotExist):
                pass

        initials['reference'] = Build.getNextBuildNumber()

        initials['parent'] = self.request.GET.get('parent', None)

        # User has provided a SalesOrder ID
        initials['sales_order'] = self.request.GET.get('sales_order', None)

        initials['quantity'] = self.request.GET.get('quantity', 1)

        return initials

    def get_data(self):
        return {
            'success': _('Created new build'),
        }

    def validate(self, build, form, **kwargs):
        """
        Perform extra form validation.

        - If part is trackable, check that either batch or serial numbers are calculated

        By this point form.is_valid() has been executed
        """

        pass


class BuildUpdate(AjaxUpdateView):
    """ View for editing a Build object """
    
    model = Build
    form_class = forms.EditBuildForm
    context_object_name = 'build'
    ajax_form_title = _('Edit Build Order Details')
    ajax_template_name = 'modal_form.html'
    role_required = 'build.change'

    def get_form(self):

        form = super().get_form()

        build = self.get_object()

        # Fields which are included in the form, but hidden
        hidden = [
            'parent',
            'sales_order',
        ]

        if build.is_complete:
            # Fields which cannot be edited once the build has been completed

            hidden += [
                'part',
                'quantity',
                'batch',
                'take_from',
                'destination',
            ]

        for field in hidden:
            form.fields[field].widget = HiddenInput()

        return form

    def get_data(self):
        return {
            'info': _('Edited build'),
        }


class BuildDelete(AjaxDeleteView):
    """ View to delete a build """

    model = Build
    ajax_template_name = 'build/delete_build.html'
    ajax_form_title = _('Delete Build Order')
    role_required = 'build.delete'


class BuildItemDelete(AjaxDeleteView):
    """ View to 'unallocate' a BuildItem.
    Really we are deleting the BuildItem object from the database.
    """

    model = BuildItem
    ajax_template_name = 'build/delete_build_item.html'
    ajax_form_title = _('Unallocate Stock')
    context_object_name = 'item'
    role_required = 'build.delete'

    def get_data(self):
        return {
            'danger': _('Removed parts from build allocation')
        }


class BuildItemCreate(AjaxCreateView):
    """
    View for allocating a StockItem to a build output.
    """

    model = BuildItem
    form_class = forms.EditBuildItemForm
    ajax_template_name = 'build/create_build_item.html'
    ajax_form_title = _('Allocate stock to build output')
    role_required = 'build.add'

    # The output StockItem against which the allocation is being made
    output = None

    # The "part" which is being allocated to the output
    part = None
    
    available_stock = None

    def get_context_data(self):
        """
        Provide context data to the template which renders the form.
        """

        ctx = super().get_context_data()

        if self.part:
            ctx['part'] = self.part

        if self.output:
            ctx['output'] = self.output

        if self.available_stock:
            ctx['stock'] = self.available_stock
        else:
            ctx['no_stock'] = True

        return ctx

    def validate(self, build_item, form, **kwargs):
        """
        Extra validation steps as required
        """

        data = form.cleaned_data

        stock_item = data.get('stock_item', None)
        quantity = data.get('quantity', None)

        if stock_item:
            # Stock item must actually be in stock!
            if not stock_item.in_stock:
                form.add_error('stock_item', _('Item must be currently in stock'))

            # Check that there are enough items available
            if quantity is not None:
                available = stock_item.unallocated_quantity()
                if quantity > available:
                    form.add_error('stock_item', _('Stock item is over-allocated'))
                    form.add_error('quantity', _('Available') + ': ' + str(normalize(available)))
        else:
            form.add_error('stock_item', _('Stock item must be selected'))

    def get_form(self):
        """ Create Form for making / editing new Part object """

        form = super(AjaxCreateView, self).get_form()

        self.build = None
        self.part = None
        self.output = None

        # If the Build object is specified, hide the input field.
        # We do not want the users to be able to move a BuildItem to a different build
        build_id = form['build'].value()

        if build_id is not None:
            """
            If the build has been provided, hide the widget to change the build selection.
            Additionally, update the allowable selections for other fields.
            """
            form.fields['build'].widget = HiddenInput()
            form.fields['install_into'].queryset = StockItem.objects.filter(build=build_id, is_building=True)
            self.build = Build.objects.get(pk=build_id)
        else:
            """
            Build has *not* been selected
            """
            pass

        # If the sub_part is supplied, limit to matching stock items
        part_id = form['part_id'].value()

        if part_id:
            try:
                self.part = Part.objects.get(pk=part_id)
       
            except (ValueError, Part.DoesNotExist):
                pass

        # If the output stock item is specified, hide the input field
        output_id = form['install_into'].value()

        if output_id is not None:

            try:
                self.output = StockItem.objects.get(pk=output_id)
                form.fields['install_into'].widget = HiddenInput()
            except (ValueError, StockItem.DoesNotExist):
                pass

        else:
            # If the output is not specified, but we know that the part is non-trackable, hide the install_into field
            if self.part and not self.part.trackable:
                form.fields['install_into'].widget = HiddenInput()

        if self.build and self.part:
            available_items = self.build.availableStockItems(self.part, self.output)

            form.fields['stock_item'].queryset = available_items

        self.available_stock = form.fields['stock_item'].queryset.all()

        # If there is only a single stockitem available, select it!
        if len(self.available_stock) == 1:
            form.fields['stock_item'].initial = self.available_stock[0].pk

        return form

    def get_initial(self):
        """ Provide initial data for BomItem. Look for the folllowing in the GET data:

        - build: pk of the Build object
        - part: pk of the Part object which we are assigning
        - output: pk of the StockItem object into which the allocated stock will be installed
        """

        initials = super(AjaxCreateView, self).get_initial().copy()

        build_id = self.get_param('build')
        part_id = self.get_param('part')
        output_id = self.get_param('install_into')

        # Reference to a Part object
        part = None

        # Reference to a StockItem object
        item = None
        
        # Reference to a Build object
        build = None

        # Reference to a StockItem object
        output = None

        if part_id:
            try:
                part = Part.objects.get(pk=part_id)
                initials['part_id'] = part.pk
            except Part.DoesNotExist:
                pass

        if build_id:
            try:
                build = Build.objects.get(pk=build_id)
                initials['build'] = build
            except Build.DoesNotExist:
                pass

        # If the output has been specified
        if output_id:
            try:
                output = StockItem.objects.get(pk=output_id)
                initials['install_into'] = output
            except (ValueError, StockItem.DoesNotExist):
                pass

        # Work out how much stock is required
        if build and part:
            required_quantity = build.unallocatedQuantity(part, output)
        else:
            required_quantity = None

        quantity = self.request.GET.get('quantity', None)

        if quantity is not None:
            quantity = float(quantity)
        elif required_quantity is not None:
            quantity = required_quantity
                
        item_id = self.get_param('item')

        # If the request specifies a particular StockItem
        if item_id:
            try:
                item = StockItem.objects.get(pk=item_id)
            except (ValueError, StockItem.DoesNotExist):
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
    ajax_template_name = 'build/edit_build_item.html'
    form_class = forms.EditBuildItemForm
    ajax_form_title = _('Edit Stock Allocation')
    role_required = 'build.change'

    def get_data(self):
        return {
            'info': _('Updated Build Item'),
        }

    def get_form(self):
        """
        Create form for editing a BuildItem.

        - Limit the StockItem options to items that match the part
        """

        form = super(BuildItemEdit, self).get_form()

        # Hide fields which we do not wish the user to edit
        for field in ['build', 'stock_item']:
            if form[field].value():
                form.fields[field].widget = HiddenInput()

        form.fields['install_into'].widget = HiddenInput()

        return form


class BuildAttachmentCreate(AjaxCreateView):
    """
    View for creating a BuildAttachment
    """

    model = BuildOrderAttachment
    form_class = forms.EditBuildAttachmentForm
    ajax_form_title = _('Add Build Order Attachment')
    role_required = 'build.add'

    def save(self, form, **kwargs):
        """
        Add information on the user that uploaded the attachment
        """

        attachment = form.save(commit=False)
        attachment.user = self.request.user
        attachment.save()

    def get_data(self):
        return {
            'success': _('Added attachment')
        }

    def get_initial(self):
        """
        Get initial data for creating an attachment
        """

        initials = super().get_initial()

        try:
            initials['build'] = Build.objects.get(pk=self.request.GET.get('build', -1))
        except (ValueError, Build.DoesNotExist):
            pass

        return initials

    def get_form(self):
        """
        Hide the 'build' field if specified
        """

        form = super().get_form()

        form.fields['build'].widget = HiddenInput()
    
        return form


class BuildAttachmentEdit(AjaxUpdateView):
    """
    View for editing a BuildAttachment object
    """

    model = BuildOrderAttachment
    form_class = forms.EditBuildAttachmentForm
    ajax_form_title = _('Edit Attachment')
    role_required = 'build.change'

    def get_form(self):
        form = super().get_form()
        form.fields['build'].widget = HiddenInput()

        return form

    def get_data(self):
        return {
            'success': _('Attachment updated')
        }


class BuildAttachmentDelete(AjaxDeleteView):
    """
    View for deleting a BuildAttachment
    """

    model = BuildOrderAttachment
    ajax_form_title = _('Delete Attachment')
    context_object_name = 'attachment'
    role_required = 'build.delete'

    def get_data(self):
        return {
            'danger': _('Deleted attachment')
        }
