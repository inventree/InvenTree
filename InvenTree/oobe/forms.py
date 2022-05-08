"""
Django Forms for interacting with oobe setups
"""

from django import forms


class CommentTextWidget(forms.TextInput):
    """Input for showing a comment as a Text field"""
    input_type = 'text'

    def render(self, name, value, attrs=None, **kwargs):
        return '' if value is None else value


class CommentTextField(forms.CharField):
    widget=CommentTextWidget
    required = False


class EmptyForm(forms.Form):
    pass


# region defaults
# TODO remove
class ContactForm3(forms.Form):
    comment = forms.CharField(
        widget=CommentTextWidget,
        required = False,
        label='Info text changed'
    )
    message1 = forms.CharField(widget=forms.Textarea)
    sender = forms.EmailField()

class ContactForm4(forms.Form):
    sender = forms.EmailField()
    message2 = forms.CharField(widget=forms.Textarea)

class ContactForm5(forms.Form):
    sender = forms.EmailField()
    sender = forms.EmailField()
    message3 = forms.CharField(widget=forms.Textarea)
# endregion
