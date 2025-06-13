"""Plugin mixin class for Supplier Integration."""

import io
from dataclasses import dataclass
from typing import Any, Generic, Optional, TypeVar

import django.contrib.auth.models
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile

import company.models
import part.models as part_models
from InvenTree.helpers_model import download_image_from_url
from plugin import PluginMixinEnum
from plugin.mixins import SettingsMixin

PartData = TypeVar('PartData')


class SupplierMixin(SettingsMixin, Generic[PartData]):
    """Mixin which provides integration to specific suppliers."""

    SUPPLIER_NAME: str

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Supplier'

    def __init__(self):
        """Register mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.SUPPLIER, True, __class__)

        self.SETTINGS['SUPPLIER'] = {
            'name': 'Supplier',
            'description': 'The Supplier which this plugin integrates with.',
            'model': 'company.company',
            'model_filters': {'is_supplier': True},
            'required': True,
        }

    @property
    def supplier(self):
        """Return the supplier company object."""
        return company.models.Company.objects.get(
            pk=self.get_setting('SUPPLIER', cache=True)
        )

    @dataclass
    class SearchResult:
        """Data class to represent a search result from a supplier."""

        sku: str
        name: str
        exact: bool
        description: Optional[str] = None
        price: Optional[str] = None
        link: Optional[str] = None
        image_url: Optional[str] = None
        id: Optional[str] = None
        existing_part: Optional[part_models.Part] = None

        def __post_init__(self):
            """Post-initialization to set the ID if not provided."""
            if not self.id:
                self.id = self.sku

    @dataclass
    class ImportParameter:
        """Data class to represent a parameter for a part during import."""

        name: str
        value: str
        on_category: Optional[bool] = False
        parameter_template: Optional[part_models.PartParameterTemplate] = None

        def __post_init__(self):
            """Post-initialization to fetch the parameter template if not provided."""
            if not self.parameter_template:
                try:
                    self.parameter_template = (
                        part_models.PartParameterTemplate.objects.get(
                            name__iexact=self.name
                        )
                    )
                except part_models.PartParameterTemplate.DoesNotExist:
                    pass

    class PartNotFoundError(Exception):
        """Exception raised when a part is not found during import."""

    class PartImportError(Exception):
        """Exception raised when an error occurs during part import."""

    # --- Methods to be overridden by plugins ---
    def get_search_results(self, term: str) -> list[SearchResult]:
        """Return a list of search results for the given search term."""
        raise NotImplementedError('This method needs to be overridden.')

    def get_import_data(self, part_id: str) -> PartData:
        """Return the import data for the given part ID."""
        raise NotImplementedError('This method needs to be overridden.')

    def get_pricing_data(self, data: PartData) -> dict[int, tuple[float, str]]:
        """Return a dictionary of pricing data for the given part data."""
        raise NotImplementedError('This method needs to be overridden.')

    def get_parameters(self, data: PartData) -> list[ImportParameter]:
        """Return a list of parameters for the given part data."""
        raise NotImplementedError('This method needs to be overridden.')

    def import_part(
        self,
        data: PartData,
        *,
        category: Optional[part_models.PartCategory],
        creation_user: Optional[django.contrib.auth.models.User],
    ) -> part_models.Part:
        """Import a part using the provided data.

        This may include:
          - Creating a new part
          - Add an image to the part
          - if this part has several variants, (create) a template part and assign it to the part
          - create related parts
          - add attachments to the part
        """
        raise NotImplementedError('This method needs to be overridden.')

    def import_manufacturer_part(
        self, data: PartData, *, part: part_models.Part
    ) -> company.models.ManufacturerPart:
        """Import a manufacturer part using the provided data.

        This may include:
          - Creating a new manufacturer
          - Creating a new manufacturer part
          - Assigning the part to the manufacturer part
          - Setting the default supplier for the part
          - Adding parameters to the manufacturer part
          - Adding attachments to the manufacturer part
        """
        raise NotImplementedError('This method needs to be overridden.')

    def import_supplier_part(
        self,
        data: PartData,
        *,
        part: part_models.Part,
        manufacturer_part: company.models.ManufacturerPart,
    ) -> part_models.SupplierPart:
        """Import a supplier part using the provided data.

        This may include:
          - Creating a new supplier part
          - Creating supplier price breaks
        """
        raise NotImplementedError('This method needs to be overridden.')

    # --- Helper methods for importing parts ---
    def download_image(self, img_url: str):
        """Download an image from the given URL and return it as a ContentFile."""
        img_r = download_image_from_url(img_url)
        fmt = img_r.format or 'PNG'
        buffer = io.BytesIO()
        img_r.save(buffer, format=fmt)

        return ContentFile(buffer.getvalue()), fmt

    def get_template_part(
        self, other_variants: list[part_models.Part], template_kwargs: dict[str, Any]
    ) -> part_models.Part:
        """Helper function to handle variant parts.

        This helper function identifies all roots for the provided 'other_variants' list
            - for no root => root part will be created using the 'template_kwargs'
            - for one root
                - root is a template => return it
                - root is no template, create a new template like if there is no root
                  and assign it to only root that was found and return it
            - for multiple roots => error raised
        """
        root_set = {v.get_root() for v in other_variants}

        # check how much roots for the variant parts exist to identify the parent_part
        parent_part = None  # part that should be used as parent_part
        root_part = None  # part that was discovered as root part in root_set
        if len(root_set) == 1:
            root_part = next(iter(root_set))
            if root_part.is_template:
                parent_part = root_part

        if len(root_set) == 0 or (root_part and not root_part.is_template):
            parent_part = part_models.Part.objects.create(**template_kwargs)

        if not parent_part:
            raise SupplierMixin.PartImportError(
                f'A few variant parts from the supplier are already imported, but have different InvenTree variant root parts, try to merge them to the same root variant template part (parts: {", ".join(str(p.pk) for p in other_variants)}).'
            )

        # assign parent_part to root_part if root_part has no variant of already
        if root_part and not root_part.is_template and not root_part.variant_of:
            root_part.variant_of = parent_part
            root_part.save()

        return parent_part

    def create_related_parts(
        self, part: part_models.Part, related_parts: list[part_models.Part]
    ):
        """Create relationships between the given part and related parts."""
        for p in related_parts:
            try:
                part_models.PartRelated.objects.create(part_1=part, part_2=p)
            except ValidationError:
                pass  # pass, duplicate relationship detected
