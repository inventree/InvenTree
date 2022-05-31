"""Helper forms which subclass Django forms to provide additional functionality."""

import logging
from urllib.parse import urlencode

from django import forms
from django.conf import settings
from django.contrib.auth.models import Group, User
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from allauth.account.adapter import DefaultAccountAdapter
from allauth.account.forms import SignupForm, set_form_field_order
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth_2fa.adapter import OTPAdapter
from allauth_2fa.utils import user_has_valid_totp_device
from crispy_forms.bootstrap import (AppendedText, Div, PrependedAppendedText,
                                    PrependedText, StrictButton)
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Field, Layout

from common.models import InvenTreeSetting
from part.models import PartCategory

logger = logging.getLogger('inventree')


class HelperForm(forms.ModelForm):
    """Provides simple integration of crispy_forms extension."""

    # Custom field decorations can be specified here, per form class
    field_prefix = {}
    field_suffix = {}
    field_placeholder = {}

    def __init__(self, *args, **kwargs):
        """Setup layout."""
        super(forms.ModelForm, self).__init__(*args, **kwargs)
        self.helper = FormHelper()

        self.helper.form_tag = False
        self.helper.form_show_errors = True

        """
        Create a default 'layout' for this form.
        Ref: https://django-crispy-forms.readthedocs.io/en/latest/layouts.html
        This is required to do fancy things later (like adding PrependedText, etc).

        Simply create a 'blank' layout for each available field.
        """

        self.rebuild_layout()

    def rebuild_layout(self):
        """Build crispy layout out of current fields."""
        layouts = []

        for field in self.fields:
            prefix = self.field_prefix.get(field, None)
            suffix = self.field_suffix.get(field, None)
            placeholder = self.field_placeholder.get(field, '')

            # Look for font-awesome icons
            if prefix and prefix.startswith('fa-'):
                prefix = r"<i class='fas {fa}'/>".format(fa=prefix)

            if suffix and suffix.startswith('fa-'):
                suffix = r"<i class='fas {fa}'/>".format(fa=suffix)

            if prefix and suffix:
                layouts.append(
                    Field(
                        PrependedAppendedText(
                            field,
                            prepended_text=prefix,
                            appended_text=suffix,
                            placeholder=placeholder
                        )
                    )
                )

            elif prefix:
                layouts.append(
                    Field(
                        PrependedText(
                            field,
                            prefix,
                            placeholder=placeholder
                        )
                    )
                )

            elif suffix:
                layouts.append(
                    Field(
                        AppendedText(
                            field,
                            suffix,
                            placeholder=placeholder
                        )
                    )
                )

            else:
                layouts.append(Field(field, placeholder=placeholder))

        self.helper.layout = Layout(*layouts)


class ConfirmForm(forms.Form):
    """Generic confirmation form."""

    confirm = forms.BooleanField(
        required=False, initial=False,
        help_text=_("Confirm")
    )

    class Meta:
        """Metaclass options."""

        fields = [
            'confirm'
        ]


class DeleteForm(forms.Form):
    """Generic deletion form which provides simple user confirmation."""

    confirm_delete = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Confirm delete'),
        help_text=_('Confirm item deletion')
    )

    class Meta:
        """Metaclass options."""

        fields = [
            'confirm_delete'
        ]


class EditUserForm(HelperForm):
    """Form for editing user information."""

    class Meta:
        """Metaclass options."""

        model = User
        fields = [
            'first_name',
            'last_name',
        ]


class SetPasswordForm(HelperForm):
    """Form for setting user password."""

    enter_password = forms.CharField(max_length=100,
                                     min_length=8,
                                     required=True,
                                     initial='',
                                     widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
                                     label=_('Enter password'),
                                     help_text=_('Enter new password'))

    confirm_password = forms.CharField(max_length=100,
                                       min_length=8,
                                       required=True,
                                       initial='',
                                       widget=forms.PasswordInput(attrs={'autocomplete': 'off'}),
                                       label=_('Confirm password'),
                                       help_text=_('Confirm new password'))

    class Meta:
        """Metaclass options."""

        model = User
        fields = [
            'enter_password',
            'confirm_password'
        ]


class SettingCategorySelectForm(forms.ModelForm):
    """Form for setting category settings."""

    category = forms.ModelChoiceField(queryset=PartCategory.objects.all())

    class Meta:
        """Metaclass options."""

        model = PartCategory
        fields = [
            'category'
        ]

    def __init__(self, *args, **kwargs):
        """Setup form layout."""
        super().__init__(*args, **kwargs)

        self.helper = FormHelper()
        # Form rendering
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Div(
                Div(Field('category'),
                    css_class='col-sm-6',
                    style='width: 70%;'),
                Div(StrictButton(_('Select Category'), css_class='btn btn-primary', type='submit'),
                    css_class='col-sm-6',
                    style='width: 30%; padding-left: 0;'),
                css_class='row',
            ),
        )


# override allauth
class CustomSignupForm(SignupForm):
    """Override to use dynamic settings."""

    def __init__(self, *args, **kwargs):
        """Check settings to influence which fields are needed."""
        kwargs['email_required'] = InvenTreeSetting.get_setting('LOGIN_MAIL_REQUIRED')

        super().__init__(*args, **kwargs)

        # check for two mail fields
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            self.fields["email2"] = forms.EmailField(
                label=_("Email (again)"),
                widget=forms.TextInput(
                    attrs={
                        "type": "email",
                        "placeholder": _("Email address confirmation"),
                    }
                ),
            )

        # check for two password fields
        if not InvenTreeSetting.get_setting('LOGIN_SIGNUP_PWD_TWICE'):
            self.fields.pop("password2")

        # reorder fields
        set_form_field_order(self, ["username", "email", "email2", "password1", "password2", ])

    def clean(self):
        """Make sure the supllied emails match if enabled in settings."""
        cleaned_data = super().clean()

        # check for two mail fields
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_MAIL_TWICE'):
            email = cleaned_data.get("email")
            email2 = cleaned_data.get("email2")
            if (email and email2) and email != email2:
                self.add_error("email2", _("You must type the same email each time."))

        return cleaned_data


class RegistratonMixin:
    """Mixin to check if registration should be enabled."""

    def is_open_for_signup(self, request, *args, **kwargs):
        """Check if signup is enabled in settings."""
        if settings.EMAIL_HOST and InvenTreeSetting.get_setting('LOGIN_ENABLE_REG', True):
            return super().is_open_for_signup(request, *args, **kwargs)
        return False

    def save_user(self, request, user, form, commit=True):
        """Check if a default group is set in settings."""
        user = super().save_user(request, user, form)
        start_group = InvenTreeSetting.get_setting('SIGNUP_GROUP')
        if start_group:
            try:
                group = Group.objects.get(id=start_group)
                user.groups.add(group)
            except Group.DoesNotExist:
                logger.error('The setting `SIGNUP_GROUP` contains an non existant group', start_group)
        user.save()
        return user


class CustomAccountAdapter(RegistratonMixin, OTPAdapter, DefaultAccountAdapter):
    """Override of adapter to use dynamic settings."""
    def send_mail(self, template_prefix, email, context):
        """Only send mail if backend configured."""
        if settings.EMAIL_HOST:
            return super().send_mail(template_prefix, email, context)
        return False


class CustomSocialAccountAdapter(RegistratonMixin, DefaultSocialAccountAdapter):
    """Override of adapter to use dynamic settings."""

    def is_auto_signup_allowed(self, request, sociallogin):
        """Check if auto signup is enabled in settings."""
        if InvenTreeSetting.get_setting('LOGIN_SIGNUP_SSO_AUTO', True):
            return super().is_auto_signup_allowed(request, sociallogin)
        return False

    # from OTPAdapter
    def has_2fa_enabled(self, user):
        """Returns True if the user has 2FA configured."""
        return user_has_valid_totp_device(user)

    def login(self, request, user):
        """Ensure user is send to 2FA before login if enabled."""
        # Require two-factor authentication if it has been configured.
        if self.has_2fa_enabled(user):
            # Cast to string for the case when this is not a JSON serializable
            # object, e.g. a UUID.
            request.session['allauth_2fa_user_id'] = str(user.id)

            redirect_url = reverse('two-factor-authenticate')
            # Add GET parameters to the URL if they exist.
            if request.GET:
                redirect_url += '?' + urlencode(request.GET)

            raise ImmediateHttpResponse(
                response=HttpResponseRedirect(redirect_url)
            )

        # Otherwise defer to the original allauth adapter.
        return super().login(request, user)
