"""
Django views for interacting with Build objects
"""

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView, ListView

from .models import Build
from . import forms

from InvenTree.views import AjaxUpdateView, AjaxDeleteView
from InvenTree.views import InvenTreeRoleMixin
from InvenTree.helpers import str2bool
from InvenTree.status_codes import BuildStatus


class BuildIndex(InvenTreeRoleMixin, ListView):
    """
    View for displaying list of Builds
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


class BuildDetail(InvenTreeRoleMixin, DetailView):
    """
    Detail view of a single Build object.
    """

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
    """
    View to delete a build
    """

    model = Build
    ajax_template_name = 'build/delete_build.html'
    ajax_form_title = _('Delete Build Order')
