"""
Django views for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ValidationError
from django.views.generic import DetailView, ListView
from django.forms import HiddenInput

from .models import Build
from . import forms
from stock.models import StockLocation, StockItem

from InvenTree.views import AjaxUpdateView, AjaxDeleteView
from InvenTree.views import InvenTreeRoleMixin
from InvenTree.helpers import str2bool, extract_serial_numbers
from InvenTree.status_codes import BuildStatus, StockStatus


class BuildIndex(InvenTreeRoleMixin, ListView):
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


class BuildOutputCreate(AjaxUpdateView):
    """
    Create a new build output (StockItem) for a given build.
    """

    model = Build
    form_class = forms.BuildOutputCreateForm
    ajax_template_name = 'build/build_output_create.html'
    ajax_form_title = _('Create Build Output')

    def validate(self, build, form, **kwargs):
        """
        Validation for the form:
        """

        quantity = form.cleaned_data.get('output_quantity', None)
        serials = form.cleaned_data.get('serial_numbers', None)

        if quantity:
            build = self.get_object()

            # Check that requested output don't exceed build remaining quantity
            maximum_output = int(build.remaining - build.incomplete_count)
            if quantity > maximum_output:
                form.add_error(
                    'output_quantity',
                    _('Maximum output quantity is ') + str(maximum_output),
                )

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
        initials['output_quantity'] = int(quantity)

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


class BuildComplete(AjaxUpdateView):
    """
    View to mark the build as complete.

    Requirements:
    - There can be no outstanding build outputs
    - The "completed" value must meet or exceed the "quantity" value
    """

    model = Build
    form_class = forms.CompleteBuildForm

    ajax_form_title = _('Complete Build Order')
    ajax_template_name = 'build/complete.html'

    def validate(self, build, form, **kwargs):

        if build.incomplete_count > 0:
            form.add_error(None, _('Build order cannot be completed - incomplete outputs remain'))

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
    - Assignes (tracked) allocated items from stock to the build output
    - Deletes pending BuildItem objects
    """

    model = Build
    form_class = forms.CompleteBuildOutputForm
    context_object_name = "build"
    ajax_form_title = _("Complete Build Output")
    ajax_template_name = "build/complete_output.html"

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
        """
        Custom validation steps for the BuildOutputComplete" form
        """

        data = form.cleaned_data

        output = data.get('output', None)

        stock_status = data.get('stock_status', StockStatus.OK)

        # Any "invalid" stock status defaults to OK
        try:
            stock_status = int(stock_status)
        except (ValueError):
            stock_status = StockStatus.OK

        if int(stock_status) not in StockStatus.keys():
            form.add_error('stock_status', _('Invalid stock status value selected'))

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
        stock_status = data.get('stock_status', StockStatus.OK)

        # Any "invalid" stock status defaults to OK
        try:
            stock_status = int(stock_status)
        except (ValueError):
            stock_status = StockStatus.OK

        # Complete the build output
        build.complete_build_output(
            output,
            self.request.user,
            location=location,
            status=stock_status,
        )

    def get_data(self):
        """ Provide feedback data back to the form """
        return {
            'success': _('Build output completed')
        }


class BuildDetail(InvenTreeRoleMixin, DetailView):
    """ Detail view of a single Build object. """

    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'

    def get_context_data(self, **kwargs):

        ctx = super(DetailView, self).get_context_data(**kwargs)

        build = self.get_object()

        ctx['bom_price'] = build.part.get_price_info(build.quantity, buy=False)
        ctx['BuildStatus'] = BuildStatus
        ctx['sub_build_count'] = build.sub_build_count()

        part = build.part
        bom_items = build.bom_items

        ctx['part'] = part
        ctx['bom_items'] = bom_items
        ctx['has_tracked_bom_items'] = build.has_tracked_bom_items()
        ctx['has_untracked_bom_items'] = build.has_untracked_bom_items()

        return ctx


class BuildDelete(AjaxDeleteView):
    """ View to delete a build """

    model = Build
    ajax_template_name = 'build/delete_build.html'
    ajax_form_title = _('Delete Build Order')
