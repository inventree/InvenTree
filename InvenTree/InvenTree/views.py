"""
Various Views which provide extra functionality over base Django Views.

In particular these views provide base functionality for rendering Django forms
as JSON objects and passing them to modal forms (using jQuery / bootstrap).
"""

import json
import os

from django.conf import settings
from django.contrib.auth.mixins import (LoginRequiredMixin,
                                        PermissionRequiredMixin)
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from django.views import View
from django.views.generic import (CreateView, DeleteView, DetailView, FormView,
                                  ListView, UpdateView)
from django.views.generic.base import RedirectView, TemplateView

from allauth.account.forms import AddEmailForm
from allauth.account.models import EmailAddress
from allauth.account.views import EmailView, PasswordResetFromKeyView
from allauth.socialaccount.forms import DisconnectForm
from allauth.socialaccount.views import ConnectionsView
from djmoney.contrib.exchange.models import ExchangeBackend, Rate
from user_sessions.views import SessionDeleteOtherView, SessionDeleteView

from common.models import ColorTheme, InvenTreeSetting
from common.settings import currency_code_default, currency_codes
from part.models import PartCategory
from users.models import RuleSet, check_user_role

from .forms import (DeleteForm, EditUserForm, SetPasswordForm,
                    SettingCategorySelectForm)
from .helpers import str2bool


def auth_request(request):
    """
    Simple 'auth' endpoint used to determine if the user is authenticated.
    Useful for (for example) redirecting authentication requests through
    django's permission framework.
    """

    if request.user.is_authenticated:
        return HttpResponse(status=200)
    else:
        return HttpResponse(status=403)


class InvenTreeRoleMixin(PermissionRequiredMixin):
    """
    Permission class based on user roles, not user 'permissions'.

    There are a number of ways that the permissions can be specified for a view:

    1.  Specify the 'role_required' attribute (e.g. part.change)
    2.  Specify the 'permission_required' attribute (e.g. part.change_bomitem)
        (Note: This is the "normal" django-esque way of doing this)
    3.  Do nothing. The mixin will attempt to "guess" what permission you require:
        a) If there is a queryset associated with the View, we have the model!
        b) The *type* of View tells us the permission level (e.g. AjaxUpdateView = change)
        c) 1 + 1 = 3
        d) Use the combination of model + permission as we would in 2)

    1.  Specify the 'role_required' attribute
        =====================================
        To specify which role is required for the mixin,
        set the class attribute 'role_required' to something like the following:

        role_required = 'part.add'
        role_required = [
            'part.change',
            'build.add',
        ]

    2.  Specify the 'permission_required' attribute
        ===========================================
        To specify a particular low-level permission,
        set the class attribute 'permission_required' to something like:

        permission_required = 'company.delete_company'

    3.  Do Nothing
        ==========

        See above.
    """

    # By default, no roles are required
    # Roles must be specified
    role_required = None

    def has_permission(self):
        """
        Determine if the current user has specified permissions
        """

        roles_required = []

        if type(self.role_required) is str:
            roles_required.append(self.role_required)
        elif type(self.role_required) in [list, tuple]:
            roles_required = self.role_required

        user = self.request.user

        # Superuser can have any permissions they desire
        if user.is_superuser:
            return True

        for required in roles_required:

            (role, permission) = required.split('.')

            if role not in RuleSet.RULESET_NAMES:
                raise ValueError(f"Role '{role}' is not a valid role")

            if permission not in RuleSet.RULESET_PERMISSIONS:
                raise ValueError(f"Permission '{permission}' is not a valid permission")

            # Return False if the user does not have *any* of the required roles
            if not check_user_role(user, role, permission):
                return False

        # If a permission_required is specified, use that!
        if self.permission_required:
            # Ignore role-based permissions
            return super().has_permission()

        # Ok, so at this point we have not explicitly require a "role" or a "permission"
        # Instead, we will use the model to introspect the data we need

        model = getattr(self, 'model', None)

        if not model:
            queryset = getattr(self, 'queryset', None)

            if queryset is not None:
                model = queryset.model

        # We were able to introspect a database model
        if model is not None:
            app_label = model._meta.app_label
            model_name = model._meta.model_name

            table = f"{app_label}_{model_name}"

            permission = self.get_permission_class()

            if not permission:
                raise AttributeError(f"permission_class not defined for {type(self).__name__}")

            # Check if the user has the required permission
            return RuleSet.check_table_permission(user, table, permission)

        # We did not fail any required checks
        return True

    def get_permission_class(self):
        """
        Return the 'permission_class' required for the current View.

        Must be one of:

        - view
        - change
        - add
        - delete

        This can either be explicitly defined, by setting the
        'permission_class' attribute,
        or it can be "guessed" by looking at the type of class
        """

        perm = getattr(self, 'permission_class', None)

        # Permission is specified by the class itself
        if perm:
            return perm

        # Otherwise, we will need to have a go at guessing...
        permission_map = {
            AjaxView: 'view',
            ListView: 'view',
            DetailView: 'view',
            UpdateView: 'change',
            DeleteView: 'delete',
            AjaxUpdateView: 'change',
            AjaxCreateView: 'add',
        }

        for view_class in permission_map.keys():

            if issubclass(type(self), view_class):
                return permission_map[view_class]

        return None


class AjaxMixin(InvenTreeRoleMixin):
    """ AjaxMixin provides basic functionality for rendering a Django form to JSON.
    Handles jsonResponse rendering, and adds extra data for the modal forms to process
    on the client side.

    Any view which inherits the AjaxMixin will need
    correct permissions set using the 'role_required' attribute

    """

    # By default, allow *any* role
    role_required = None

    # By default, point to the modal_form template
    # (this can be overridden by a child class)
    ajax_template_name = 'modal_form.html'

    ajax_form_title = ''

    def get_form_title(self):
        """ Default implementation - return the ajax_form_title variable """
        return self.ajax_form_title

    def get_param(self, name, method='GET'):
        """ Get a request query parameter value from URL e.g. ?part=3

        Args:
            name: Variable name e.g. 'part'
            method: Request type ('GET' or 'POST')

        Returns:
            Value of the supplier parameter or None if parameter is not available
        """

        if method == 'POST':
            return self.request.POST.get(name, None)
        else:
            return self.request.GET.get(name, None)

    def get_data(self):
        """ Get extra context data (default implementation is empty dict)

        Returns:
            dict object (empty)
        """
        return {}

    def validate(self, obj, form, **kwargs):
        """
        Hook for performing custom form validation steps.

        If a form error is detected, add it to the form,
        with 'form.add_error()'

        Ref: https://docs.djangoproject.com/en/dev/topics/forms/
        """

        # Do nothing by default
        pass

    def renderJsonResponse(self, request, form=None, data=None, context=None):
        """ Render a JSON response based on specific class context.

        Args:
            request: HTTP request object (e.g. GET / POST)
            form: Django form object (may be None)
            data: Extra JSON data to pass to client
            context: Extra context data to pass to template rendering

        Returns:
            JSON response object
        """
        # a empty dict as default can be dangerous - set it here if empty
        if not data:
            data = {}

        if not request.is_ajax():
            return HttpResponseRedirect('/')

        if context is None:
            try:
                context = self.get_context_data()
            except AttributeError:
                context = {}

        # If no 'form' argument is supplied, look at the underlying class
        if form is None:
            try:
                form = self.get_form()
            except AttributeError:
                pass

        if form:
            context['form'] = form
        else:
            context['form'] = None

        data['title'] = self.get_form_title()

        data['html_form'] = render_to_string(
            self.ajax_template_name,
            context,
            request=request
        )

        # Custom feedback`data
        fb = self.get_data()

        for key in fb.keys():
            data[key] = fb[key]

        return JsonResponse(data, safe=False)


class AjaxView(AjaxMixin, View):
    """ An 'AJAXified' View for displaying an object
    """

    def post(self, request, *args, **kwargs):
        return self.renderJsonResponse(request)

    def get(self, request, *args, **kwargs):

        return self.renderJsonResponse(request)


class QRCodeView(AjaxView):
    """ An 'AJAXified' view for displaying a QR code.

    Subclasses should implement the get_qr_data(self) function.
    """

    ajax_template_name = "qr_code.html"

    def get(self, request, *args, **kwargs):
        self.request = request
        self.pk = self.kwargs['pk']
        return self.renderJsonResponse(request, None, context=self.get_context_data())

    def get_qr_data(self):
        """ Returns the text object to render to a QR code.
        The actual rendering will be handled by the template """

        return None

    def get_context_data(self):
        """ Get context data for passing to the rendering template.

        Explicity passes the parameter 'qr_data'
        """

        context = {}

        qr = self.get_qr_data()

        if qr:
            context['qr_data'] = qr
        else:
            context['error_msg'] = 'Error generating QR code'

        return context


class AjaxCreateView(AjaxMixin, CreateView):

    """ An 'AJAXified' CreateView for creating a new object in the db
    - Returns a form in JSON format (for delivery to a modal window)
    - Handles form validation via AJAX POST requests
    """

    def get(self, request, *args, **kwargs):
        """ Creates form with initial data, and renders JSON response """

        super(CreateView, self).get(request, *args, **kwargs)

        self.request = request
        form = self.get_form()
        return self.renderJsonResponse(request, form)

    def save(self, form):
        """
        Method for actually saving the form to the database.
        Default implementation is very simple,
        but can be overridden if required.
        """

        self.object = form.save()

        return self.object

    def post(self, request, *args, **kwargs):
        """ Responds to form POST. Validates POST data and returns status info.

        - Validate POST form data
        - If valid, save form
        - Return status info (success / failure)
        """
        self.request = request
        self.form = self.get_form()

        # Perform initial form validation
        self.form.is_valid()

        # Perform custom validation (no object can be provided yet)
        self.validate(None, self.form)

        valid = self.form.is_valid()

        # Extra JSON data sent alongside form
        data = {
            'form_valid': valid,
            'form_errors': self.form.errors.as_json(),
            'non_field_errors': self.form.non_field_errors().as_json(),
        }

        # Add in any extra class data
        for value, key in enumerate(self.get_data()):
            data[key] = value

        if valid:

            # Save the object to the database
            self.object = self.save(self.form)

            if self.object:
                # Return the PK of the newly-created object
                data['pk'] = self.object.pk
                data['text'] = str(self.object)

                try:
                    data['url'] = self.object.get_absolute_url()
                except AttributeError:
                    pass

        return self.renderJsonResponse(request, self.form, data)


class AjaxUpdateView(AjaxMixin, UpdateView):
    """ An 'AJAXified' UpdateView for updating an object in the db
    - Returns form in JSON format (for delivery to a modal window)
    - Handles repeated form validation (via AJAX) until the form is valid
    """

    def get(self, request, *args, **kwargs):
        """ Respond to GET request.

        - Populates form with object data
        - Renders form to JSON and returns to client
        """

        super(UpdateView, self).get(request, *args, **kwargs)

        return self.renderJsonResponse(request, self.get_form(), context=self.get_context_data())

    def save(self, object, form, **kwargs):
        """
        Method for updating the object in the database.
        Default implementation is very simple, but can be overridden if required.

        Args:
            object - The current object, to be updated
            form - The validated form
        """

        self.object = form.save()

        return self.object

    def post(self, request, *args, **kwargs):
        """ Respond to POST request.

        - Updates model with POST field data
        - Performs form and object validation
        - If errors exist, re-render the form
        - Otherwise, return sucess status
        """

        self.request = request

        # Make sure we have an object to point to
        self.object = self.get_object()

        form = self.get_form()

        # Perform initial form validation
        form.is_valid()

        # Perform custom validation
        self.validate(self.object, form)

        valid = form.is_valid()

        data = {
            'form_valid': valid,
            'form_errors': form.errors.as_json(),
            'non_field_errors': form.non_field_errors().as_json(),
        }

        # Add in any extra class data
        for value, key in enumerate(self.get_data()):
            data[key] = value

        if valid:

            # Save the updated objec to the database
            self.save(self.object, form)

            self.object = self.get_object()

            # Include context data about the updated object
            data['pk'] = self.object.pk

            try:
                data['url'] = self.object.get_absolute_url()
            except AttributeError:
                pass

        return self.renderJsonResponse(request, form, data)


class AjaxDeleteView(AjaxMixin, UpdateView):

    """ An 'AJAXified DeleteView for removing an object from the DB
    - Returns a HTML object (not a form!) in JSON format (for delivery to a modal window)
    - Handles deletion
    """

    form_class = DeleteForm
    ajax_form_title = _("Delete Item")
    ajax_template_name = "modal_delete_form.html"
    context_object_name = 'item'

    def get_object(self):
        try:
            self.object = self.model.objects.get(pk=self.kwargs['pk'])
        except:
            return None
        return self.object

    def get_form(self):
        return self.form_class(self.get_form_kwargs())

    def get(self, request, *args, **kwargs):
        """ Respond to GET request

        - Render a DELETE confirmation form to JSON
        - Return rendered form to client
        """

        super(UpdateView, self).get(request, *args, **kwargs)

        form = self.get_form()

        context = self.get_context_data()

        context[self.context_object_name] = self.get_object()

        return self.renderJsonResponse(request, form, context=context)

    def post(self, request, *args, **kwargs):
        """ Respond to POST request

        - DELETE the object
        - Render success message to JSON and return to client
        """

        obj = self.get_object()
        pk = obj.id

        form = self.get_form()

        confirmed = str2bool(request.POST.get('confirm_delete', False))
        context = self.get_context_data()

        if confirmed:
            obj.delete()
        else:
            form.add_error('confirm_delete', _('Check box to confirm item deletion'))
            context[self.context_object_name] = self.get_object()

        data = {
            'id': pk,
            'form_valid': confirmed
        }

        return self.renderJsonResponse(request, form, data=data, context=context)


class EditUserView(AjaxUpdateView):
    """ View for editing user information """

    ajax_template_name = "modal_form.html"
    ajax_form_title = _("Edit User Information")
    form_class = EditUserForm

    def get_object(self):
        return self.request.user


class SetPasswordView(AjaxUpdateView):
    """ View for setting user password """

    ajax_template_name = "InvenTree/password.html"
    ajax_form_title = _("Set Password")
    form_class = SetPasswordForm

    def get_object(self):
        return self.request.user

    def post(self, request, *args, **kwargs):

        form = self.get_form()

        valid = form.is_valid()

        p1 = request.POST.get('enter_password', '')
        p2 = request.POST.get('confirm_password', '')

        if valid:
            # Passwords must match

            if p1 != p2:
                error = _('Password fields must match')
                form.add_error('enter_password', error)
                form.add_error('confirm_password', error)

                valid = False

        data = {
            'form_valid': valid
        }

        if valid:
            user = self.request.user

            user.set_password(p1)
            user.save()

        return self.renderJsonResponse(request, form, data=data)


class IndexView(TemplateView):
    """ View for InvenTree index page """

    template_name = 'InvenTree/index.html'

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        return context


class SearchView(TemplateView):
    """ View for InvenTree search page.

    Displays results of search query
    """

    template_name = 'InvenTree/search.html'

    def post(self, request, *args, **kwargs):
        """ Handle POST request (which contains search query).

        Pass the search query to the page template
        """

        context = self.get_context_data()

        query = request.POST.get('search', '')

        context['query'] = query

        return super(TemplateView, self).render_to_response(context)


class DynamicJsView(TemplateView):
    """
    View for returning javacsript files,
    which instead of being served dynamically,
    are passed through the django translation engine!
    """

    template_name = ""
    content_type = 'text/javascript'


class SettingsView(TemplateView):
    """ View for configuring User settings
    """

    template_name = "InvenTree/settings/settings.html"

    def get_context_data(self, **kwargs):

        ctx = super().get_context_data(**kwargs).copy()

        ctx['settings'] = InvenTreeSetting.objects.all().order_by('key')

        ctx["base_currency"] = currency_code_default()
        ctx["currencies"] = currency_codes

        ctx["rates"] = Rate.objects.filter(backend="InvenTreeExchange")

        ctx["categories"] = PartCategory.objects.all().order_by('tree_id', 'lft', 'name')

        # When were the rates last updated?
        try:
            backend = ExchangeBackend.objects.get(name='InvenTreeExchange')
            ctx["rates_updated"] = backend.last_update
        except:
            ctx["rates_updated"] = None

        # load locale stats
        STAT_FILE = os.path.abspath(os.path.join(settings.BASE_DIR, 'InvenTree/locale_stats.json'))
        try:
            ctx["locale_stats"] = json.load(open(STAT_FILE, 'r'))
        except:
            ctx["locale_stats"] = {}

        # Forms and context for allauth
        ctx['add_email_form'] = AddEmailForm
        ctx["can_add_email"] = EmailAddress.objects.can_add_email(self.request.user)

        # Form and context for allauth social-accounts
        ctx["request"] = self.request
        ctx['social_form'] = DisconnectForm(request=self.request)

        # user db sessions
        ctx['session_key'] = self.request.session.session_key
        ctx['session_list'] = self.request.user.session_set.filter(expire_date__gt=now()).order_by('-last_activity')

        return ctx


class AllauthOverrides(LoginRequiredMixin):
    """
    Override allauths views to always redirect to success_url
    """
    def get(self, request, *args, **kwargs):
        # always redirect to settings
        return HttpResponseRedirect(self.success_url)


class CustomEmailView(AllauthOverrides, EmailView):
    """
    Override of allauths EmailView to always show the settings but leave the functions allow
    """
    success_url = reverse_lazy("settings")


class CustomConnectionsView(AllauthOverrides, ConnectionsView):
    """
    Override of allauths ConnectionsView to always show the settings but leave the functions allow
    """
    success_url = reverse_lazy("settings")


class CustomPasswordResetFromKeyView(PasswordResetFromKeyView):
    """
    Override of allauths PasswordResetFromKeyView to always show the settings but leave the functions allow
    """
    success_url = reverse_lazy("account_login")


class UserSessionOverride():
    """overrides sucessurl to lead to settings"""
    def get_success_url(self):
        return str(reverse_lazy('settings'))


class CustomSessionDeleteView(UserSessionOverride, SessionDeleteView):
    pass


class CustomSessionDeleteOtherView(UserSessionOverride, SessionDeleteOtherView):
    pass


class CurrencyRefreshView(RedirectView):
    """
    POST endpoint to refresh / update exchange rates
    """

    url = reverse_lazy("settings-currencies")

    def post(self, request, *args, **kwargs):
        """
        On a POST request we will attempt to refresh the exchange rates
        """

        from InvenTree.tasks import offload_task, update_exchange_rates

        offload_task(update_exchange_rates, force_sync=True)

        return redirect(reverse_lazy('settings'))


class AppearanceSelectView(RedirectView):
    """ View for selecting a color theme """

    def get_user_theme(self):
        """ Get current user color theme """
        try:
            user_theme = ColorTheme.objects.filter(user=self.request.user).get()
        except ColorTheme.DoesNotExist:
            user_theme = None

        return user_theme

    def post(self, request, *args, **kwargs):
        """ Save user color theme selection """

        theme = request.POST.get('theme', None)

        # Get current user theme
        user_theme = self.get_user_theme()

        # Create theme entry if user did not select one yet
        if not user_theme:
            user_theme = ColorTheme()
            user_theme.user = request.user

        user_theme.name = theme
        user_theme.save()

        return redirect(reverse_lazy('settings'))


class SettingCategorySelectView(FormView):
    """ View for selecting categories in settings """

    form_class = SettingCategorySelectForm
    success_url = reverse_lazy('settings-category')
    template_name = "InvenTree/settings/category.html"

    def get_initial(self):
        """ Set category selection """

        initial = super().get_initial()

        category = self.request.GET.get('category', None)
        if category:
            initial['category'] = category

        return initial

    def post(self, request, *args, **kwargs):
        """ Handle POST request (which contains category selection).

        Pass the selected category to the page template
        """

        form = self.get_form()

        if form.is_valid():
            context = self.get_context_data()

            context['category'] = form.cleaned_data['category']

            return super(SettingCategorySelectView, self).render_to_response(context)

        return self.form_invalid(form)


class DatabaseStatsView(AjaxView):
    """ View for displaying database statistics """

    ajax_template_name = "stats.html"
    ajax_form_title = _("System Information")


class NotificationsView(TemplateView):
    """ View for showing notifications
    """

    template_name = "InvenTree/notifications/notifications.html"
