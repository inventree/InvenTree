"""Views for OOBE"""
from django.http import Http404
from django.shortcuts import render
from django.urls import reverse

from common.views import NamedMultiStepFormView

from . import forms
from oobe.registry import setups


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
        context['title'] = f'{self.setup_context.title} | {self.step.title}'
        return context
    # endregion

    @property
    def step(self):
        """The current steps page"""
        if hasattr(self, 'setup_context') and hasattr(self, 'kwargs') and self.kwargs.get('step'):
            return self.setup_context.pages[self.kwargs["step"]]

        # This should never happen - raise if it does to caution against wrong dev moves
        raise Http404()

    def _set_form_list(self):
        """Helper function to make sure the dynamic form_list is used"""
        if self.from_list_overriden:
            return

        # Update form_list to use the setup (referenced by slug)
        self.set_setup_context()

        # Check if steps are valid
        self.form_list = self.get_initkwargs(self.setup_context.form_list, url_name=self.url_name).get('form_list')
        self.from_list_overriden = True

    def set_setup_context(self):
        """Set the setup context for the current context"""
        # Check if setup slug is valid
        reference = self.kwargs.get('setup', None)
        if not reference:
            raise Http404()

        # Get context
        self.setup_context = setups.get(reference)
        if not self.setup_context:
            raise Http404()
        return self.setup_context

    def done(self, form_list, **kwargs):
        print(kwargs)

        return render(self.request, 'oobe/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'success_message': self.setup_context.done,
        })
