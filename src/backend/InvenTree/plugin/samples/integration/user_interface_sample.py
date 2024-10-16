"""Sample plugin which demonstrates user interface integrations."""

import random
import time

from django.utils.translation import gettext_lazy as _

from InvenTree.version import INVENTREE_SW_VERSION
from part.models import Part
from plugin import InvenTreePlugin
from plugin.helpers import render_template, render_text
from plugin.mixins import SettingsMixin, UserInterfaceMixin


class SampleUserInterfacePlugin(SettingsMixin, UserInterfaceMixin, InvenTreePlugin):
    """A sample plugin which demonstrates user interface integrations."""

    NAME = 'SampleUI'
    SLUG = 'sampleui'
    TITLE = 'Sample User Interface Plugin'
    DESCRIPTION = 'A sample plugin which demonstrates user interface integrations'
    VERSION = '1.1'

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

    def get_ui_panels(self, instance_type: str, instance_id: int, request, **kwargs):
        """Return a list of custom panels to be injected into the UI."""
        panels = []

        # First, add a custom panel which will appear on every type of page
        # This panel will contain a simple message

        content = render_text(
            """
            This is a <i>sample panel</i> which appears on every page.
            It renders a simple string of <b>HTML</b> content.

            <br>
            <h5>Instance Details:</h5>
            <ul>
            <li>Instance Type: {{ instance_type }}</li>
            <li>Instance ID: {{ instance_id }}</li>
            </ul>
            """,
            context={'instance_type': instance_type, 'instance_id': instance_id},
        )

        panels.append({
            'name': 'sample_panel',
            'label': 'Sample Panel',
            'content': content,
        })

        # A broken panel which tries to load a non-existent JS file
        if instance_id is not None and self.get_setting('ENABLE_BROKEN_PANElS'):
            panels.append({
                'name': 'broken_panel',
                'label': 'Broken Panel',
                'source': '/this/does/not/exist.js',
            })

        # A dynamic panel which will be injected into the UI (loaded from external file)
        # Note that we additionally provide some "context" data to the front-end render function
        if self.get_setting('ENABLE_DYNAMIC_PANEL'):
            panels.append({
                'name': 'dynamic_panel',
                'label': 'Dynamic Part Panel',
                'source': self.plugin_static_file('sample_panel.js'),
                'context': {
                    'version': INVENTREE_SW_VERSION,
                    'plugin_version': self.VERSION,
                    'random': random.randint(1, 100),
                    'time': time.time(),
                },
                'icon': 'part',
            })

        # Next, add a custom panel which will appear on the 'part' page
        # Note that this content is rendered from a template file,
        # using the django templating system
        if self.get_setting('ENABLE_PART_PANELS') and instance_type == 'part':
            try:
                part = Part.objects.get(pk=instance_id)
            except (Part.DoesNotExist, ValueError):
                part = None

            # Note: This panel will *only* be available if the part is active
            if part and part.active:
                content = render_template(
                    self, 'uidemo/custom_part_panel.html', context={'part': part}
                )

                panels.append({
                    'name': 'part_panel',
                    'label': 'Part Panel',
                    'content': content,
                })

        # Next, add a custom panel which will appear on the 'purchaseorder' page
        if (
            self.get_setting('ENABLE_PURCHASE_ORDER_PANELS')
            and instance_type == 'purchaseorder'
        ):
            panels.append({
                'name': 'purchase_order_panel',
                'label': 'Purchase Order Panel',
                'content': 'This is a custom panel which appears on the <b>Purchase Order</b> view page.',
            })

        return panels

    def get_ui_features(self, feature_type, context, request):
        """Return a list of custom features to be injected into the UI."""
        if (
            feature_type == 'template_editor'
            and context.get('template_type') == 'labeltemplate'
        ):
            return [
                {
                    'feature_type': 'template_editor',
                    'options': {
                        'key': 'sample-template-editor',
                        'title': 'Sample Template Editor',
                        'icon': 'keywords',
                    },
                    'source': '/static/plugin/sample_template.js:getTemplateEditor',
                }
            ]

        if feature_type == 'template_preview':
            return [
                {
                    'feature_type': 'template_preview',
                    'options': {
                        'key': 'sample-template-preview',
                        'title': 'Sample Template Preview',
                        'icon': 'category',
                    },
                    'source': '/static/plugin/sample_template.js:getTemplatePreview',
                }
            ]

        return []

    def get_admin_context(self) -> dict:
        """Return custom context data which can be rendered in the admin panel."""
        return {'apple': 'banana', 'foo': 'bar', 'hello': 'world'}
