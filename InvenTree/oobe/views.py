from common.views import NamedMultiStepFormView

from .forms import ContactForm1, ContactForm2


class ContactWizard(NamedMultiStepFormView):
    form_list = [ContactForm1, ContactForm2]
    template_name = 'oobe/setup.html'

    def done(self, form_list, **kwargs):
        print(form_list)
        print(kwargs)
