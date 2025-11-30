"""Ruleset definitions which control the InvenTree user permissions."""

from django.conf import settings
from django.utils.translation import gettext_lazy as _

from generic.enums import StringEnum


class RuleSetEnum(StringEnum):
    """Enumeration of ruleset names."""

    ADMIN = 'admin'
    PART_CATEGORY = 'part_category'
    PART = 'part'
    STOCK_LOCATION = 'stock_location'
    STOCK = 'stock'
    BUILD = 'build'
    PURCHASE_ORDER = 'purchase_order'
    SALES_ORDER = 'sales_order'
    RETURN_ORDER = 'return_order'


# This is a list of all the ruleset choices available in the system.
# These are used to determine the permissions available to a group of users.
RULESET_CHOICES = [
    (RuleSetEnum.ADMIN, _('Admin')),
    (RuleSetEnum.PART_CATEGORY, _('Part Categories')),
    (RuleSetEnum.PART, _('Parts')),
    (RuleSetEnum.STOCK_LOCATION, _('Stock Locations')),
    (RuleSetEnum.STOCK, _('Stock Items')),
    (RuleSetEnum.BUILD, _('Build Orders')),
    (RuleSetEnum.PURCHASE_ORDER, _('Purchase Orders')),
    (RuleSetEnum.SALES_ORDER, _('Sales Orders')),
    (RuleSetEnum.RETURN_ORDER, _('Return Orders')),
]

# Ruleset names available in the system.
RULESET_NAMES = [choice[0] for choice in RULESET_CHOICES]

# Permission types available for each ruleset.
RULESET_PERMISSIONS = ['view', 'add', 'change', 'delete']

RULESET_CHANGE_INHERIT = [('part', 'bomitem')]


def get_ruleset_models() -> dict:
    """Return a dictionary of models associated with each ruleset.

    This function maps particular database models to each ruleset.
    """
    ruleset_models = {
        RuleSetEnum.ADMIN: [
            'auth_group',
            'auth_user',
            'auth_permission',
            'users_apitoken',
            'users_ruleset',
            'report_labeltemplate',
            'report_reportasset',
            'report_reportsnippet',
            'report_reporttemplate',
            'account_emailaddress',
            'account_emailconfirmation',
            'socialaccount_socialaccount',
            'socialaccount_socialapp',
            'socialaccount_socialtoken',
            'otp_totp_totpdevice',
            'otp_static_statictoken',
            'otp_static_staticdevice',
            'mfa_authenticator',
            # Oauth
            'oauth2_provider_application',
            'oauth2_provider_grant',
            'oauth2_provider_idtoken',
            'oauth2_provider_accesstoken',
            'oauth2_provider_refreshtoken',
            # Plugins
            'plugin_pluginconfig',
            'plugin_pluginsetting',
            'plugin_pluginusersetting',
            # Misc
            'common_barcodescanresult',
            'common_newsfeedentry',
            'taggit_tag',
            'taggit_taggeditem',
            'flags_flagstate',
            'machine_machineconfig',
            'machine_machinesetting',
            # common / comms
            'common_emailmessage',
            'common_emailthread',
            'django_mailbox_mailbox',
            'django_mailbox_messageattachment',
            'django_mailbox_message',
        ],
        RuleSetEnum.PART_CATEGORY: [
            'part_partcategory',
            'part_partcategoryparametertemplate',
            'part_partcategorystar',
        ],
        RuleSetEnum.PART: [
            'part_part',
            'part_partpricing',
            'part_bomitem',
            'part_bomitemsubstitute',
            'part_partsellpricebreak',
            'part_partinternalpricebreak',
            'part_parttesttemplate',
            'part_partrelated',
            'part_partstar',
            'part_partstocktake',
            'part_partcategorystar',
            'company_supplierpart',
            'company_manufacturerpart',
        ],
        RuleSetEnum.STOCK_LOCATION: ['stock_stocklocation', 'stock_stocklocationtype'],
        RuleSetEnum.STOCK: [
            'stock_stockitem',
            'stock_stockitemtracking',
            'stock_stockitemtestresult',
        ],
        RuleSetEnum.BUILD: [
            'part_part',
            'part_partcategory',
            'part_bomitem',
            'part_bomitemsubstitute',
            'build_build',
            'build_builditem',
            'build_buildline',
            'stock_stockitem',
            'stock_stocklocation',
        ],
        RuleSetEnum.PURCHASE_ORDER: [
            'company_company',
            'company_contact',
            'company_address',
            'company_manufacturerpart',
            'company_supplierpart',
            'company_supplierpricebreak',
            'order_purchaseorder',
            'order_purchaseorderlineitem',
            'order_purchaseorderextraline',
        ],
        RuleSetEnum.SALES_ORDER: [
            'company_company',
            'company_contact',
            'company_address',
            'order_salesorder',
            'order_salesorderallocation',
            'order_salesorderlineitem',
            'order_salesorderextraline',
            'order_salesordershipment',
        ],
        RuleSetEnum.RETURN_ORDER: [
            'company_company',
            'company_contact',
            'company_address',
            'order_returnorder',
            'order_returnorderlineitem',
            'order_returnorderextraline',
        ],
    }

    if settings.SITE_MULTI:
        ruleset_models['admin'].append('sites_site')

    return ruleset_models


def get_ruleset_ignore() -> list[str]:
    """Return a list of database tables which do not require permissions."""
    return [
        # Core django models (not user configurable)
        'admin_logentry',
        'contenttypes_contenttype',
        # Models which currently do not require permissions
        'common_attachment',
        'common_parametertemplate',
        'common_parameter',
        'common_customunit',
        'common_dataoutput',
        'common_inventreesetting',
        'common_inventreeusersetting',
        'common_notificationentry',
        'common_notificationmessage',
        'common_notesimage',
        'common_projectcode',
        'common_webhookendpoint',
        'common_webhookmessage',
        'common_inventreecustomuserstatemodel',
        'common_selectionlistentry',
        'common_selectionlist',
        'users_owner',
        'users_userprofile',  # User profile is handled in the serializer - only own user can change
        # Third-party tables
        'error_report_error',
        'exchange_rate',
        'exchange_exchangebackend',
        'usersessions_usersession',
        'sessions_session',
        # Django-q
        'django_q_ormq',
        'django_q_failure',
        'django_q_task',
        'django_q_schedule',
        'django_q_success',
        # Importing
        'importer_dataimportsession',
        'importer_dataimportcolumnmap',
        'importer_dataimportrow',
    ]
