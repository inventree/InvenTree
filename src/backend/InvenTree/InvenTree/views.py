"""Various Views which provide extra functionality over base Django Views.

In particular these views provide base functionality for rendering Django forms
as JSON objects and passing them to modal forms (using jQuery / bootstrap).
"""

from django.contrib.auth.mixins import PermissionRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.template.loader import render_to_string
from django.views import View
from django.views.generic import DeleteView, DetailView, ListView, UpdateView

from users.models import RuleSet, check_user_role

from .helpers import is_ajax


def auth_request(request):
    """Simple 'auth' endpoint used to determine if the user is authenticated.

    Useful for (for example) redirecting authentication requests through django's permission framework.
    """
    if request.user.is_authenticated:
        return HttpResponse(status=200)
    return HttpResponse(status=403)


class InvenTreeRoleMixin(PermissionRequiredMixin):
    """Permission class based on user roles, not user 'permissions'.

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
        """Determine if the current user has specified permissions."""
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

            table = f'{app_label}_{model_name}'

            permission = self.get_permission_class()

            if not permission:
                raise AttributeError(
                    f'permission_class not defined for {type(self).__name__}'
                )

            # Check if the user has the required permission
            return RuleSet.check_table_permission(user, table, permission)

        # We did not fail any required checks
        return True

    def get_permission_class(self):
        """Return the 'permission_class' required for the current View.

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
        }

        for view_class in permission_map:
            if issubclass(type(self), view_class):
                return permission_map[view_class]

        return None


class AjaxMixin(InvenTreeRoleMixin):
    """AjaxMixin provides basic functionality for rendering a Django form to JSON. Handles jsonResponse rendering, and adds extra data for the modal forms to process on the client side.

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
        """Default implementation - return the ajax_form_title variable."""
        return self.ajax_form_title

    def get_param(self, name, method='GET'):
        """Get a request query parameter value from URL e.g. ?part=3.

        Args:
            name: Variable name e.g. 'part'
            method: Request type ('GET' or 'POST')

        Returns:
            Value of the supplier parameter or None if parameter is not available
        """
        if method == 'POST':
            return self.request.POST.get(name, None)
        return self.request.GET.get(name, None)

    def get_data(self):
        """Get extra context data (default implementation is empty dict).

        Returns:
            dict object (empty)
        """
        return {}

    def validate(self, obj, form, **kwargs):
        """Hook for performing custom form validation steps.

        If a form error is detected, add it to the form,
        with 'form.add_error()'

        Ref: https://docs.djangoproject.com/en/dev/topics/forms/
        """
        # Do nothing by default

    def renderJsonResponse(self, request, form=None, data=None, context=None):
        """Render a JSON response based on specific class context.

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

        if not is_ajax(request):
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
            self.ajax_template_name, context, request=request
        )

        # Custom feedback`data
        fb = self.get_data()

        for key in fb:
            data[key] = fb[key]

        return JsonResponse(data, safe=False)


class AjaxView(AjaxMixin, View):
    """An 'AJAXified' View for displaying an object."""

    def post(self, request, *args, **kwargs):
        """Return a json formatted response.

        This renderJsonResponse function must be supplied by your function.
        """
        return self.renderJsonResponse(request)

    def get(self, request, *args, **kwargs):
        """Return a json formatted response.

        This renderJsonResponse function must be supplied by your function.
        """
        return self.renderJsonResponse(request)


class AjaxUpdateView(AjaxMixin, UpdateView):
    """An 'AJAXified' UpdateView for updating an object in the db.

    - Returns form in JSON format (for delivery to a modal window)
    - Handles repeated form validation (via AJAX) until the form is valid
    """

    def get(self, request, *args, **kwargs):
        """Respond to GET request.

        - Populates form with object data
        - Renders form to JSON and returns to client
        """
        super(UpdateView, self).get(request, *args, **kwargs)

        return self.renderJsonResponse(
            request, self.get_form(), context=self.get_context_data()
        )

    def save(self, obj, form, **kwargs):
        """Method for updating the object in the database. Default implementation is very simple, but can be overridden if required.

        Args:
            obj: The current object, to be updated
            form: The validated form

        Returns:
            object instance for supplied form
        """
        self.object = form.save()

        return self.object

    def post(self, request, *args, **kwargs):
        """Respond to POST request.

        - Updates model with POST field data
        - Performs form and object validation
        - If errors exist, re-render the form
        - Otherwise, return success status
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
            # Save the updated object to the database
            self.save(self.object, form)

            self.object = self.get_object()

            # Include context data about the updated object
            data['pk'] = self.object.pk

            try:
                data['url'] = self.object.get_absolute_url()
            except AttributeError:
                pass

        return self.renderJsonResponse(request, form, data)
