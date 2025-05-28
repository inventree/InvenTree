# inven_tree_custom/dispatch/forms.py
from django import forms
from .models import Dispatch, DispatchItem

class DispatchForm(forms.ModelForm):
    class Meta:
        model = Dispatch
        fields = ['client', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}), # HTML5 date picker
        }

class AddStockItemToDispatchForm(forms.Form):
    # This form will be used later for the scanning/adding item functionality
    # It's not directly tied to a model in the same way as ModelForm.
    product_number = forms.CharField(
        label="Product Number / Scan Code",
        max_length=100,
        widget=forms.TextInput(attrs={'placeholder': 'Enter or scan product number'})
    )
    quantity = forms.DecimalField(
        initial=1.0,
        min_value=0.01 # Or based on requirements
    )
    # dispatch_id will be typically passed in the view, not as a visible form field
