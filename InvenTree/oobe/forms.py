"""Django Forms for interacting with oobe setups."""

from django import forms


class CommentTextWidget(forms.TextInput):
    """Input for showing a comment as a Text field."""
    input_type = 'text'

    def render(self, name, value, attrs=None, **kwargs):
        """Override render to not retrun None but '' if empty."""
        return '' if value is None else value


class CommentTextField(forms.CharField):
    """FormField that shows only the label of a textfield."""
    widget = CommentTextWidget
    required = False


class EmptyForm(forms.Form):
    """Empty form as dafault for setups."""
    pass
