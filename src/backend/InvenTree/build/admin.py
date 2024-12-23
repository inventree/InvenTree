"""Admin functionality for the BuildOrder app."""

from django.contrib import admin

from import_export import widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

import part.models
from build.models import Build, BuildItem, BuildLine
from InvenTree.admin import InvenTreeResource


class BuildResource(InvenTreeResource):
    """Class for managing import/export of Build data."""

    # For some reason, we need to specify the fields individually for this ModelResource,
    # but we don't for other ones.
    # TODO: 2022-05-12 - Need to investigate why this is the case!

    class Meta:
        """Metaclass options."""

        models = Build
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True
        exclude = ['lft', 'rght', 'tree_id', 'level', 'metadata']

    id = Field(attribute='pk', widget=widgets.IntegerWidget())

    reference = Field(attribute='reference')

    title = Field(attribute='title')

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(part.models.Part))

    part_name = Field(attribute='part__full_name', readonly=True)

    overdue = Field(
        attribute='is_overdue', readonly=True, widget=widgets.BooleanWidget()
    )

    completed = Field(attribute='completed', readonly=True)

    quantity = Field(attribute='quantity')

    status = Field(attribute='status')

    batch = Field(attribute='batch')

    notes = Field(attribute='notes')


@admin.register(Build)
class BuildAdmin(ImportExportModelAdmin):
    """Class for managing the Build model via the admin interface."""

    exclude = ['reference_int']

    list_display = ('reference', 'title', 'part', 'status', 'batch', 'quantity')

    search_fields = ['reference', 'title', 'part__name', 'part__description']

    autocomplete_fields = ['parent', 'part', 'sales_order', 'take_from', 'destination']


@admin.register(BuildItem)
class BuildItemAdmin(admin.ModelAdmin):
    """Class for managing the BuildItem model via the admin interface."""

    list_display = ('stock_item', 'quantity')

    autocomplete_fields = ['build_line', 'stock_item', 'install_into']


@admin.register(BuildLine)
class BuildLineAdmin(admin.ModelAdmin):
    """Class for managing the BuildLine model via the admin interface."""

    list_display = ('build', 'bom_item', 'quantity')

    search_fields = ['build__title', 'build__reference', 'bom_item__sub_part__name']
