from common.views import MultiStepFormView

from .forms import ContactForm1, ContactForm2


class ContactWizard(MultiStepFormView):
    form_list = [ContactForm1, ContactForm2]
    template_name = 'oobe/setup.html'

    def done(self, form_list, **kwargs):
        print(form_list)
        print(kwargs)
