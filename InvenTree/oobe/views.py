
from django.shortcuts import render
from django.utils.translation import gettext_lazy as _

from common.views import NamedMultiStepFormView

from .forms import ContactForm1, ContactForm2


class SetupWizard(NamedMultiStepFormView):
    form_list = [ContactForm1, ContactForm2]
    template_name = 'oobe/setup.html'

    def done(self, form_list, **kwargs):

        return render(self.request, 'oobe/done.html', {
            'form_data': [form.cleaned_data for form in form_list],
            'success_message': _('Done with initial setup'),
        })
