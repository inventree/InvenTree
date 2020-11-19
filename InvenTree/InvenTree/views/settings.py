from django.views.generic.base import TemplateView
from django.views.generic import FormView
from common.models import InvenTreeSetting
from common.signals import admin_nav_event
from django.utils.translation import gettext_lazy as _
from itertools import groupby
from django.apps import apps
from django.shortcuts import redirect
from ..forms import SettingCategorySelectForm
from django.urls import reverse_lazy


class SettingsBaseView(TemplateView):
    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs).copy()
        request = self.request
        ctx['extension_nav'] = sorted(
            sum((list(a[1]) for a in admin_nav_event.send(self, request=request)), []),
            key=lambda r: (1 if r.get('parent') else 0, r['label'])
        )

        return ctx


class SettingsView(SettingsBaseView):
    """ View for configuring User settings
    """

    template_name = "InvenTree/settings.html"

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs).copy()

        ctx['settings'] = InvenTreeSetting.objects.all().order_by('key')

        return ctx


class ExtensionsView(SettingsBaseView):
    """ View for managing extensions
    """

    template_name = "InvenTree/settings/extensions.html"

    def get_context_data(self, **kwargs):
        from InvenTree.extensions import get_all_extensions

        context = super().get_context_data(**kwargs)
        extensions = [e for e in get_all_extensions(self) if not
                      e.name.startswith('.') and getattr(e, 'visible', True)]

        order = [
            'FEATURE',
            'PAYMENT',
            'INTEGRATION',
            'CUSTOMIZATION',
            'FORMAT',
            'API',
        ]
        labels = {
            'FEATURE': _('Features'),
            'PAYMENT': _('Payment providers'),
            'INTEGRATION': _('Integrations'),
            'CUSTOMIZATION': _('Customizations'),
            'FORMAT': _('Output and export formats'),
            'API': _('API features'),
        }
        context['extensions'] = sorted([
            (c, labels.get(c, c), list(plist))
            for c, plist
            in groupby(
                sorted(extensions, key=lambda e: str(getattr(e, 'category', _('Other')))),
                lambda e: str(getattr(e, 'category', _('Other')))
            )
        ], key=lambda c: (order.index(c[0]), c[1]) if c[0] in order else (999, str(c[1])))
        return context

    def post(self, request, *args, **kwargs):
        from InvenTree.extensions import get_all_extensions

        extensions_available = [e.app.name for e in get_all_extensions(self) if not
                                e.name.startswith('.') and getattr(e, 'visible', True)]

        for key, value in request.POST.items():
            if key.startswith("extension:"):
                module = key.split(":")[1]
                app_name = key.split(":")[1].split(".")[-1]
                app = apps.get_app_config(app_name)
                if value == "enable" and module in extensions_available:
                    app.enable()
                else:
                    app.disable()

        return redirect(request.path_info)


class SettingCategorySelectView(FormView):
    """ View for selecting categories in settings """

    form_class = SettingCategorySelectForm
    success_url = reverse_lazy('settings-category')
    template_name = "InvenTree/settings/category.html"

    def get_initial(self):
        """ Set category selection """

        initial = super(SettingCategorySelectView, self).get_initial()

        category = self.request.GET.get('category', None)
        if category:
            initial['category'] = category

        return initial

    def post(self, request, *args, **kwargs):
        """ Handle POST request (which contains category selection).

        Pass the selected category to the page template
        """

        form = self.get_form()

        if form.is_valid():
            context = self.get_context_data()

            context['category'] = form.cleaned_data['category']

            return super(SettingCategorySelectView, self).render_to_response(context)

        return self.form_invalid(form)
