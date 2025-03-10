"""Sample plugin which demonstrates user interface integrations."""

import random
import time

from django.utils.translation import gettext_lazy as _

from InvenTree.version import INVENTREE_SW_VERSION
from part.models import Part
from plugin import InvenTreePlugin
from plugin.mixins import SettingsMixin, UserInterfaceMixin


class SampleUserInterfacePlugin(SettingsMixin, UserInterfaceMixin, InvenTreePlugin):
    """A sample plugin which demonstrates user interface integrations."""

    NAME = 'SampleUI'
    SLUG = 'sampleui'
    TITLE = 'Sample User Interface Plugin'
    DESCRIPTION = 'A sample plugin which demonstrates user interface integrations'
    VERSION = '2.0'

    ADMIN_SOURCE = 'ui_settings.js'

    SETTINGS = {
        'ENABLE_PART_PANELS': {
            'name': _('Enable Part Panels'),
            'description': _('Enable custom panels for Part views'),
            'default': True,
            'validator': bool,
        },
        'ENABLE_PURCHASE_ORDER_PANELS': {
            'name': _('Enable Purchase Order Panels'),
            'description': _('Enable custom panels for Purchase Order views'),
            'default': False,
            'validator': bool,
        },
        'ENABLE_BROKEN_PANELS': {
            'name': _('Enable Broken Panels'),
            'description': _('Enable broken panels for testing'),
            'default': True,
            'validator': bool,
        },
        'ENABLE_DYNAMIC_PANEL': {
            'name': _('Enable Dynamic Panel'),
            'description': _('Enable dynamic panels for testing'),
            'default': True,
            'validator': bool,
        },
    }

    def get_ui_panels(self, request, context, **kwargs):
        """Return a list of custom panels to be injected into the UI."""
        panels = []
        context = context or {}

        # First, add a custom panel which will appear on every type of page
        # This panel will contain a simple message

        target_model = context.get('target_model', None)
        target_id = context.get('target_id', None)

        # A broken panel which tries to load a non-existent JS file
        if target_id is not None and self.get_setting('ENABLE_BROKEN_PANElS'):
            panels.append({
                'key': 'broken-panel',
                'title': 'Broken Panel',
                'source': '/this/does/not/exist.js',
            })

        # A dynamic panel which will be injected into the UI (loaded from external file)
        # Note that we additionally provide some "context" data to the front-end render function
        if self.get_setting('ENABLE_DYNAMIC_PANEL'):
            panels.append({
                'key': 'dynamic-panel',
                'title': 'Dynamic Panel',
                'source': self.plugin_static_file('sample_panel.js'),
                'icon': 'ti:wave-saw-tool:outline',
                'context': {
                    'version': INVENTREE_SW_VERSION,
                    'plugin_version': self.VERSION,
                    'random': random.randint(1, 100),
                    'time': time.time(),
                },
            })

        # Next, add a custom panel which will appear on the 'part' page
        # Note that this content is rendered from a template file,
        # using the django templating system
        if self.get_setting('ENABLE_PART_PANELS') and target_model == 'part':
            try:
                part = Part.objects.get(pk=target_id)
            except (Part.DoesNotExist, ValueError):
                part = None

            panels.append({
                'key': 'part-panel',
                'title': _('Part Panel'),
                'source': self.plugin_static_file('sample_panel.js:renderPartPanel'),
                'icon': 'ti:package_outline',
                'context': {'part_name': part.name if part else ''},
            })

        # Next, add a custom panel which will appear on the 'purchaseorder' page
        if target_model == 'purchaseorder' and self.get_setting(
            'ENABLE_PURCHASE_ORDER_PANELS'
        ):
            panels.append({
                'key': 'purchase_order_panel',
                'title': 'Purchase Order Panel',
                'source': self.plugin_static_file('sample_panel.js:renderPoPanel'),
            })

        # Admin panel - only visible to admin users
        if request.user.is_superuser:
            panels.append({
                'key': 'admin-panel',
                'title': 'Admin Panel',
                'source': self.plugin_static_file(
                    'sample_panel.js:renderAdminOnlyPanel'
                ),
            })

        return panels

    def get_ui_dashboard_items(self, request, context, **kwargs):
        """Return a list of custom dashboard items."""
        items = [
            {
                'key': 'broken-dashboard-item',
                'title': _('Broken Dashboard Item'),
                'description': _(
                    'This is a broken dashboard item - it will not render!'
                ),
                'source': '/this/does/not/exist.js',
            },
            {
                'key': 'sample-dashboard-item',
                'title': _('Sample Dashboard Item'),
                'description': _(
                    'This is a sample dashboard item. It renders a simple string of HTML content.'
                ),
                'source': self.plugin_static_file('sample_dashboard_item.js'),
            },
            {
                'key': 'dynamic-dashboard-item',
                'title': _('Context Dashboard Item'),
                'description': 'A dashboard item which passes context data from the server',
                'source': self.plugin_static_file(
                    'sample_dashboard_item.js:renderContextItem'
                ),
                'context': {'foo': 'bar', 'hello': 'world'},
                'options': {'width': 3, 'height': 2},
            },
        ]

        # Admin item - only visible to users with superuser access
        if request.user.is_superuser:
            items.append({
                'key': 'admin-dashboard-item',
                'title': _('Admin Dashboard Item'),
                'description': _('This is an admin-only dashboard item.'),
                'source': self.plugin_static_file('admin_dashboard_item.js'),
                'options': {'width': 4, 'height': 2},
                'context': {'secret-key': 'this-is-a-secret'},
            })

        return items

    def get_ui_template_editors(self, request, context, **kwargs):
        """Return a list of custom template editors."""
        # If the context is a label template, return a custom template editor
        if context.get('template_type') == 'labeltemplate':
            return [
                {
                    'key': 'sample-template-editor',
                    'title': 'Sample Template Editor',
                    'icon': 'keywords',
                    'source': self.plugin_static_file(
                        'sample_template.js:getTemplateEditor'
                    ),
                }
            ]

        return []

    def get_ui_template_previews(self, request, context, **kwargs):
        """Return a list of custom template previews."""
        return [
            {
                'key': 'sample-template-preview',
                'title': 'Sample Template Preview',
                'icon': 'category',
                'source': self.plugin_static_file(
                    'sample_preview.js:getTemplatePreview'
                ),
            }
        ]

    def get_admin_context(self) -> dict:
        """Return custom context data which can be rendered in the admin panel."""
        return {'apple': 'banana', 'foo': 'bar', 'hello': 'world'}
