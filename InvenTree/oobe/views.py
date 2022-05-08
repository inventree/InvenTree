"""Views for OOBE"""
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from common.views import NamedMultiStepFormView

from . import forms


global_form_list = {
    'abc': {
        'steps': [
            forms.ContactForm3,
            forms.ContactForm4,
            forms.ContactForm5,
        ],
        'done': _('Done with initial setup'),
        'title': _('Testtitle'),
    },
}


class SetupWizard(NamedMultiStepFormView):
    form_list = [forms.EmptyForm, ]
    template_name = 'oobe/setup.html'

    # region overrides
    @classmethod
    def get_initkwargs(cls, *args, **kwargs):
        """Override form_list if not supplied"""
        if not args and not hasattr(kwargs, 'form_list'):
            kwargs['form_list'] = cls.form_list
        return super().get_initkwargs(*args, **kwargs)

    def __init__(self, *args, **kwargs):
        """Set dynamic flags"""
        self.from_list_overriden = False
        super().__init__(*args, **kwargs)

    def get_form_list(self):
        """Make sure the dynamic form_list is used"""
        self._set_form_list()
        return super().get_form_list()

    def get_form(self, step=None, data=None, files=None):
        """Make sure the dynamic form_list is used"""
        self._set_form_list()
        return super().get_form(step, data, files)

    def get_step_url(self, step):
        """Override url lookup to introduce current setup into lookup"""
        return reverse(self.url_name, kwargs={'step': step, 'setup': self.kwargs.get('setup')})

    def get_context_data(self, **kwargs):
        """Override to add setup title to context"""
        context = super().get_context_data(**kwargs)
        context['title'] = self.setup_context.get('title')
        return context
    # endregion

    def _set_form_list(self):
        """Helper function to make sure the dynamic form_list is used"""
        if self.from_list_overriden:
            return

        # Update form_list to use the setup (referenced by slug)
        self.set_setup_context()

        # Check if steps are valid
        steps = self.setup_context.get('steps')
        self.form_list = self.get_initkwargs(steps, url_name=self.url_name).get('form_list')
        self.from_list_overriden = True

    def set_setup_context(self):
        """Set the setup context for the current context"""
        # Check if setup slug is valid
        reference = self.kwargs.get('setup', None)
        if not reference:
            raise Http404()

        # Get context
        context = global_form_list.get(reference, None)
        if not context:
            raise Http404()

        # Set context
        self.setup_context = context

    def done(self, form_list, **kwargs):
        print(kwargs)

        return render(self.request, 'oobe/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'success_message': self.setup_context.get('done'),
        })
