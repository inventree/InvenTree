"""System settings for part app."""

from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _

import common.validators
import part.validators
from common.setting.type import InvenTreeSettingsKeyType, SettingFlag


def reset_part_name_format(setting):
    """Clear the cached Part 'full_name' template when PART_NAME_FORMAT changes."""
    from part.helpers import reset_full_name_template

    reset_full_name_template()


SYSTEM_SETTINGS: dict[str, InvenTreeSettingsKeyType] = {
    'PART_ENABLE_LOCKING': {
        'name': _('Part Locking'),
        'description': _('Enable locking of parts to prevent modification'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.TOGGLE],
    },
    'PART_ENABLE_REVISION': {
        'name': _('Part Revisions'),
        'description': _('Enable revision field for Part'),
        'validator': bool,
        'default': True,
        'flags': [SettingFlag.TOGGLE],
    },
    'PART_REVISION_ASSEMBLY_ONLY': {
        'name': _('Assembly Revision Only'),
        'description': _('Only allow revisions for assembly parts'),
        'validator': bool,
        'default': False,
    },
    'PART_ALLOW_DELETE_FROM_ASSEMBLY': {
        'name': _('Allow Deletion from Assembly'),
        'description': _('Allow deletion of parts which are used in an assembly'),
        'validator': bool,
        'default': False,
    },
    'PART_IPN_REGEX': {
        'name': _('IPN Regex'),
        'description': _(
            'Regular expression pattern for matching Part IPN. The pattern may match any part of the IPN: use ^ and $ to match the whole value. Parts without an IPN are not checked.'
        ),
        'default': '',
        'validator': part.validators.validate_ipn_regex,
    },
    'PART_ALLOW_DUPLICATE_IPN': {
        'name': _('Allow Duplicate IPN'),
        'description': _('Allow multiple parts to share the same IPN'),
        'default': True,
        'validator': bool,
    },
    'PART_ALLOW_EDIT_IPN': {
        'name': _('Allow Editing IPN'),
        'description': _('Allow changing the IPN value while editing a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_BOM': {
        'name': _('Copy Part BOM Data'),
        'description': _('Copy BOM data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_PARAMETERS': {
        'name': _('Copy Part Parameter Data'),
        'description': _('Copy parameter data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_COPY_TESTS': {
        'name': _('Copy Part Test Data'),
        'description': _('Copy test data by default when duplicating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_CATEGORY_PARAMETERS': {
        'name': _('Copy Category Parameter Templates'),
        'description': _('Copy category parameter templates when creating a part'),
        'default': True,
        'validator': bool,
    },
    'PART_TEMPLATE': {
        'name': _('Template'),
        'description': _('Parts are templates by default'),
        'default': False,
        'validator': bool,
    },
    'PART_ASSEMBLY': {
        'name': _('Assembly'),
        'description': _('Parts can be assembled from other components by default'),
        'default': False,
        'validator': bool,
    },
    'PART_COMPONENT': {
        'name': _('Component'),
        'description': _('Parts can be used as sub-components by default'),
        'default': True,
        'validator': bool,
    },
    'PART_PURCHASEABLE': {
        'name': _('Purchaseable'),
        'description': _('Parts are purchaseable by default'),
        'default': True,
        'validator': bool,
    },
    'PART_SALABLE': {
        'name': _('Salable'),
        'description': _('Parts are salable by default'),
        'default': False,
        'validator': bool,
    },
    'PART_TRACKABLE': {
        'name': _('Trackable'),
        'description': _('Parts are trackable by default'),
        'default': False,
        'validator': bool,
    },
    'PART_VIRTUAL': {
        'name': _('Virtual'),
        'description': _('Parts are virtual by default'),
        'default': False,
        'validator': bool,
    },
    'PART_CREATE_INITIAL': {
        'name': _('Initial Stock Data'),
        'description': _('Allow creation of initial stock when adding a new part'),
        'default': False,
        'validator': bool,
    },
    'PART_CREATE_SUPPLIER': {
        'name': _('Initial Supplier Data'),
        'description': _(
            'Allow creation of initial supplier data when adding a new part'
        ),
        'default': True,
        'validator': bool,
    },
    'PART_NAME_FORMAT': {
        'name': _('Part Name Display Format'),
        'description': _('Format to display the part name'),
        'default': "{{ part.IPN if part.IPN }}{{ ' | ' if part.IPN }}{{ part.name }}{{ ' | ' if part.revision }}"
        '{{ part.revision if part.revision }}',
        'validator': part.validators.validate_part_name_format,
        'after_save': reset_part_name_format,
    },
    'PART_CATEGORY_DEFAULT_ICON': {
        'name': _('Part Category Default Icon'),
        'description': _('Part category default icon (empty means no icon)'),
        'default': '',
        'validator': common.validators.validate_icon,
    },
    'PART_INTERNAL_PRICE': {
        'name': _('Internal Prices'),
        'description': _('Enable internal prices for parts'),
        'default': False,
        'validator': bool,
    },
    'PART_BOM_USE_INTERNAL_PRICE': {
        'name': _('Internal Price Override'),
        'description': _(
            'If available, internal prices override price range calculations'
        ),
        'default': False,
        'validator': bool,
    },
    'PART_BOM_ALLOW_ZERO_QUANTITY': {
        'name': _('Allow BOM Zero Quantity'),
        'description': _(
            'Accept a zero quantity for BOM item for part. Enables using setup quantity to define a quantity required per build, independent of build quantity'
        ),
        'default': False,
        'validator': bool,
    },
    'STOCKTAKE_ENABLE': {
        'name': _('Enable Stocktake'),
        'description': _(
            'Enable functionality for recording historical stock levels and value'
        ),
        'flags': [SettingFlag.TOGGLE],
        'validator': bool,
        'default': False,
    },
    'STOCKTAKE_EXCLUDE_EXTERNAL': {
        'name': _('Exclude External Locations'),
        'description': _(
            'Exclude stock items in external locations from stocktake calculations'
        ),
        'validator': bool,
        'default': False,
    },
    'STOCKTAKE_AUTO_DAYS': {
        'name': _('Automatic Stocktake Period'),
        'description': _(
            'Number of days between automatic stocktake recording (set to zero to disable)'
        ),
        'validator': [int, MinValueValidator(0)],
        'default': 7,
        'units': _('days'),
    },
    'STOCKTAKE_DELETE_OLD_ENTRIES': {
        'name': _('Delete Old Stocktake Entries'),
        'description': _(
            'Delete stocktake entries older than the specified number of days'
        ),
        'default': False,
        'validator': bool,
    },
    'STOCKTAKE_DELETE_DAYS': {
        'name': _('Stocktake Deletion Interval'),
        'description': _(
            'Stocktake entries will be deleted after specified number of days'
        ),
        'default': 365,
        'units': _('days'),
        'validator': [int, MinValueValidator(30)],
    },
}
