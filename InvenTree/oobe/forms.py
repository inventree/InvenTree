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
    widget = CommentTextWidget
    required = False


class EmptyForm(forms.Form):
    pass
