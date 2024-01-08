"""Admin classes for the 'users' app"""

from django import forms
from django.contrib import admin, messages
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import Group
from django.utils.translation import gettext_lazy as _

from users.models import ApiToken, Owner, RuleSet

User = get_user_model()


@admin.register(ApiToken)
class ApiTokenAdmin(admin.ModelAdmin):
    """Admin class for the ApiToken model."""

    list_display = ('token', 'user', 'name', 'expiry', 'active')
    list_filter = ('user', 'revoked')
    fields = ('token', 'user', 'name', 'created', 'last_seen', 'revoked', 'expiry', 'metadata')

    def get_fields(self, request, obj=None):
        """Return list of fields to display."""

        if obj:
            fields = ['token',]
        else:
            fields = ['key',]

        fields += ['user', 'name', 'created', 'last_seen', 'revoked', 'expiry', 'metadata']

        return fields

    def get_readonly_fields(self, request, obj=None):
        """Some fields are read-only after creation"""

        ro = ['created', 'last_seen']

        if obj:
            ro += ['token', 'user', 'expiry', 'name']

        return ro


class RuleSetInline(admin.TabularInline):
    """Class for displaying inline RuleSet data in the Group admin page."""

    model = RuleSet
    can_delete = False
    verbose_name = 'Ruleset'
    verbose_plural_name = 'Rulesets'
    fields = ['name'] + list(RuleSet.RULE_OPTIONS)
    readonly_fields = ['name']
    max_num = len(RuleSet.RULESET_CHOICES)
    min_num = 1
    extra = 0
    # TODO: find better way to order inlines
    ordering = ['name']


class InvenTreeGroupAdminForm(forms.ModelForm):
    """Custom admin form for the Group model.

    Adds the ability for editing user membership directly in the group admin page.
    """

    class Meta:
        """Metaclass defines extra fields"""
        model = Group
        exclude = []
        fields = [
            'name',
            'users',
        ]

    def __init__(self, *args, **kwargs):  # pragma: no cover
        """Populate the 'users' field with the users in the current group"""
        super().__init__(*args, **kwargs)

        if self.instance.pk:
            # Populate the users field with the current Group users.
            self.fields['users'].initial = self.instance.user_set.all()

    # Add the users field.
    users = forms.ModelMultipleChoiceField(
        queryset=User.objects.all(),
        required=False,
        widget=FilteredSelectMultiple('users', False),
        label=_('Users'),
        help_text=_('Select which users are assigned to this group')
    )

    def save_m2m(self):  # pragma: no cover
        """Add the users to the Group"""
        self.instance.user_set.set(self.cleaned_data['users'])

    def save(self, *args, **kwargs):  # pragma: no cover
        """Custom save method for Group admin form"""
        # Default save
        instance = super().save()
        # Save many-to-many data
        self.save_m2m()
        return instance


class RoleGroupAdmin(admin.ModelAdmin):  # pragma: no cover
    """Custom admin interface for the Group model."""

    form = InvenTreeGroupAdminForm

    inlines = [
        RuleSetInline,
    ]

    list_display = ('name', 'admin', 'part_category', 'part', 'stocktake', 'stock_location',
                    'stock_item', 'build', 'purchase_order', 'sales_order', 'return_order')

    def get_rule_set(self, obj, rule_set_type):
        """Return list of permissions for the given ruleset."""
        # Get all rulesets associated to object
        rule_sets = RuleSet.objects.filter(group=obj.pk)

        # Select ruleset based on type
        for rule_set in rule_sets:
            if rule_set.name == rule_set_type:
                break

        def append_permission_level(permission_level, next_level):
            """Append permission level"""
            if not permission_level:
                return next_level

            if permission_level[:-1].endswith('|'):
                permission_level += next_level
            else:
                permission_level += ' | ' + next_level

            return permission_level

        permission_level = ''

        if rule_set.can_view:
            permission_level = append_permission_level(permission_level, 'V')

        if rule_set.can_add:
            permission_level = append_permission_level(permission_level, 'A')

        if rule_set.can_change:
            permission_level = append_permission_level(permission_level, 'C')

        if rule_set.can_delete:
            permission_level = append_permission_level(permission_level, 'D')

        return permission_level

    def admin(self, obj):
        """Return the ruleset for the admin role"""
        return self.get_rule_set(obj, 'admin')

    def part_category(self, obj):
        """Return the ruleset for the PartCategory role"""
        return self.get_rule_set(obj, 'part_category')

    def part(self, obj):
        """Return the ruleset for the Part role"""
        return self.get_rule_set(obj, 'part')

    def stocktake(self, obj):
        """Return the ruleset for the Stocktake role"""
        return self.get_rule_set(obj, 'stocktake')

    def stock_location(self, obj):
        """Return the ruleset for the StockLocation role"""
        return self.get_rule_set(obj, 'stock_location')

    def stock_item(self, obj):
        """Return the ruleset for the StockItem role"""
        return self.get_rule_set(obj, 'stock')

    def build(self, obj):
        """Return the ruleset for the BuildOrder role"""
        return self.get_rule_set(obj, 'build')

    def purchase_order(self, obj):
        """Return the ruleset for the PurchaseOrder role"""
        return self.get_rule_set(obj, 'purchase_order')

    def sales_order(self, obj):
        """Return the ruleset for the SalesOrder role"""
        return self.get_rule_set(obj, 'sales_order')

    def return_order(self, obj):
        """Return the ruleset ofr the ReturnOrder role"""
        return self.get_rule_set(obj, 'return_order')

    def get_formsets_with_inlines(self, request, obj=None):
        """Return all inline formsets"""
        for inline in self.get_inline_instances(request, obj):
            # Hide RuleSetInline in the 'Add role' view
            if not isinstance(inline, RuleSetInline) or obj is not None:
                yield inline.get_formset(request, obj), inline

    filter_horizontal = ['permissions']

    def save_model(self, request, obj, form, change):
        """Save overwrite.

        This method serves two purposes:
            - show warning message whenever the group users belong to multiple groups
            - skip saving of the group instance model as inlines needs to be saved before.
        """
        # Get form cleaned data
        users = form.cleaned_data['users']

        # Check for users who are members of multiple groups
        multiple_group_users = []

        for user in users:
            if user.groups.all().count() > 1:
                multiple_group_users.append(user.username)

        # If any, display warning message when group is saved
        if len(multiple_group_users) > 0:

            msg = _("The following users are members of multiple groups") + ": " + ", ".join(multiple_group_users)

            messages.add_message(
                request,
                messages.WARNING,
                msg
            )

    def save_formset(self, request, form, formset, change):
        """Save the inline formset"""
        # Save inline Rulesets
        formset.save()
        # Save Group instance and update permissions
        form.instance.save(update_fields=['name'])


class InvenTreeUserAdmin(UserAdmin):
    """Custom admin page for the User model.

    Hides the "permissions" view as this is now handled
    entirely by groups and RuleSets.

    (And it's confusing!)
    """
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'last_login')  # display last connection for each user in user admin panel.
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email')}),
        (_('Permissions'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups'),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Owner)
class OwnerAdmin(admin.ModelAdmin):
    """Custom admin interface for the Owner model."""
    pass


admin.site.unregister(Group)
admin.site.register(Group, RoleGroupAdmin)

admin.site.unregister(User)
admin.site.register(User, InvenTreeUserAdmin)
