"""Django views for interacting with Build objects."""

from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView, ListView

from .models import Build

from InvenTree.views import AjaxDeleteView
from InvenTree.views import InvenTreeRoleMixin
from InvenTree.status_codes import BuildStatus

from plugin.views import InvenTreePluginViewMixin


class BuildIndex(InvenTreeRoleMixin, ListView):
    """View for displaying list of Builds."""
    model = Build
    template_name = 'build/index.html'
    context_object_name = 'builds'

    def get_queryset(self):
        """Return all Build objects (order by date, newest first)"""
        return Build.objects.order_by('status', '-completion_date')


class BuildDetail(InvenTreeRoleMixin, InvenTreePluginViewMixin, DetailView):
    """Detail view of a single Build object."""

    model = Build
    template_name = 'build/detail.html'
    context_object_name = 'build'

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs)

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
    """View to delete a build."""

    model = Build
    ajax_template_name = 'build/delete_build.html'
    ajax_form_title = _('Delete Build Order')
