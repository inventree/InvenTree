"""Admin class for the 'company' app"""

from django.contrib import admin

from import_export import widgets
from import_export.admin import ImportExportModelAdmin
from import_export.fields import Field

from InvenTree.admin import InvenTreeResource
from part.models import Part

from .models import (
    Address,
    Company,
    Contact,
    ManufacturerPart,
    ManufacturerPartAttachment,
    ManufacturerPartParameter,
    SupplierPart,
    SupplierPriceBreak,
)


class CompanyResource(InvenTreeResource):
    """Class for managing Company data import/export."""

    class Meta:
        """Metaclass defines extra options"""

        model = Company
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True


class CompanyAdmin(ImportExportModelAdmin):
    """Admin class for the Company model"""

    resource_class = CompanyResource

    list_display = ('name', 'website', 'contact')

    search_fields = ['name', 'description']


class SupplierPartResource(InvenTreeResource):
    """Class for managing SupplierPart data import/export."""

    class Meta:
        """Metaclass defines extra admin options"""

        model = SupplierPart
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    part_name = Field(attribute='part__full_name', readonly=True)

    supplier = Field(attribute='supplier', widget=widgets.ForeignKeyWidget(Company))

    supplier_name = Field(attribute='supplier__name', readonly=True)


class SupplierPriceBreakInline(admin.TabularInline):
    """Inline for supplier-part pricing"""

    model = SupplierPriceBreak


class SupplierPartAdmin(ImportExportModelAdmin):
    """Admin class for the SupplierPart model"""

    resource_class = SupplierPartResource

    list_display = ('part', 'supplier', 'SKU')

    search_fields = ['supplier__name', 'part__name', 'manufacturer_part__MPN', 'SKU']

    inlines = [SupplierPriceBreakInline]

    autocomplete_fields = ('part', 'supplier', 'manufacturer_part')


class ManufacturerPartResource(InvenTreeResource):
    """Class for managing ManufacturerPart data import/export."""

    class Meta:
        """Metaclass defines extra admin options"""

        model = ManufacturerPart
        skip_unchanged = True
        report_skipped = True
        clean_model_instances = True

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(Part))

    part_name = Field(attribute='part__full_name', readonly=True)

    manufacturer = Field(
        attribute='manufacturer', widget=widgets.ForeignKeyWidget(Company)
    )

    manufacturer_name = Field(attribute='manufacturer__name', readonly=True)


class ManufacturerPartAdmin(ImportExportModelAdmin):
    """Admin class for ManufacturerPart model."""

    resource_class = ManufacturerPartResource

    list_display = ('part', 'manufacturer', 'MPN')

    search_fields = ['manufacturer__name', 'part__name', 'MPN']

    autocomplete_fields = ('part', 'manufacturer')


class ManufacturerPartAttachmentAdmin(ImportExportModelAdmin):
    """Admin class for ManufacturerPartAttachment model."""

    list_display = ('manufacturer_part', 'attachment', 'comment')

    autocomplete_fields = ('manufacturer_part',)


class ManufacturerPartParameterResource(InvenTreeResource):
    """Class for managing ManufacturerPartParameter data import/export."""

    class Meta:
        """Metaclass defines extra admin options"""

        model = ManufacturerPartParameter
        skip_unchanged = True
        report_skipped = True
        clean_model_instance = True


class ManufacturerPartParameterAdmin(ImportExportModelAdmin):
    """Admin class for ManufacturerPartParameter model."""

    resource_class = ManufacturerPartParameterResource

    list_display = ('manufacturer_part', 'name', 'value')

    search_fields = ['manufacturer_part__manufacturer__name', 'name', 'value']

    autocomplete_fields = ('manufacturer_part',)


class SupplierPriceBreakResource(InvenTreeResource):
    """Class for managing SupplierPriceBreak data import/export."""

    class Meta:
        """Metaclass defines extra admin options"""

        model = SupplierPriceBreak
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

    part = Field(attribute='part', widget=widgets.ForeignKeyWidget(SupplierPart))

    supplier_id = Field(attribute='part__supplier__pk', readonly=True)

    supplier_name = Field(attribute='part__supplier__name', readonly=True)

    part_name = Field(attribute='part__part__full_name', readonly=True)

    SKU = Field(attribute='part__SKU', readonly=True)

    MPN = Field(attribute='part__MPN', readonly=True)


class SupplierPriceBreakAdmin(ImportExportModelAdmin):
    """Admin class for the SupplierPriceBreak model"""

    resource_class = SupplierPriceBreakResource

    list_display = ('part', 'quantity', 'price')

    autocomplete_fields = ('part',)


class AddressResource(InvenTreeResource):
    """Class for managing Address data import/export"""

    class Meta:
        """Metaclass defining extra options"""

        model = Address
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

    company = Field(attribute='company', widget=widgets.ForeignKeyWidget(Company))


class AddressAdmin(ImportExportModelAdmin):
    """Admin class for the Address model"""

    resource_class = AddressResource

    list_display = ('company', 'line1', 'postal_code', 'country')

    search_fields = ['company', 'country', 'postal_code']


class ContactResource(InvenTreeResource):
    """Class for managing Contact data import/export"""

    class Meta:
        """Metaclass defining extra options"""

        model = Contact
        skip_unchanged = True
        report_skipped = False
        clean_model_instances = True

    company = Field(attribute='company', widget=widgets.ForeignKeyWidget(Company))


class ContactAdmin(ImportExportModelAdmin):
    """Admin class for the Contact model"""

    resource_class = ContactResource

    list_display = ('company', 'name', 'role', 'email', 'phone')

    search_fields = ['company', 'name', 'email']


admin.site.register(Company, CompanyAdmin)
admin.site.register(SupplierPart, SupplierPartAdmin)
admin.site.register(SupplierPriceBreak, SupplierPriceBreakAdmin)

admin.site.register(ManufacturerPart, ManufacturerPartAdmin)
admin.site.register(ManufacturerPartAttachment, ManufacturerPartAttachmentAdmin)
admin.site.register(ManufacturerPartParameter, ManufacturerPartParameterAdmin)

admin.site.register(Address, AddressAdmin)
admin.site.register(Contact, ContactAdmin)
