"""Dataclasses for supplier plugins."""

from dataclasses import dataclass
from typing import Optional

import common.models
import part.models as part_models


@dataclass
class Supplier:
    """Data class to represent a supplier.

    Note that one plugin can connect to multiple suppliers this way with e.g. different credentials.

    Attributes:
        slug (str): A unique identifier for the supplier.
        name (str): The human-readable name of the supplier.
    """

    slug: str
    name: str


@dataclass
class SearchResult:
    """Data class to represent a search result from a supplier.

    Attributes:
        sku (str): The stock keeping unit identifier for the part.
        name (str): The name of the part.
        exact (bool): Indicates if the search result is an exact match.
        description (Optional[str]): A brief description of the part.
        price (Optional[str]): The price of the part as a string.
        link (Optional[str]): A URL link to the part on the supplier's website.
        image_url (Optional[str]): A URL to an image of the part.
        id (Optional[str]): An optional identifier for the part (part_id), defaults to sku if not provided
        existing_part (Optional[part_models.Part]): An existing part in the system that matches this search result, if any.
    """

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
    """Data class to represent a parameter for a part during import.

    Attributes:
        name (str): The name of the parameter.
        value (str): The value of the parameter.
        on_category (Optional[bool]): Indicates if the parameter is associated with a category. This will be automatically set by InvenTree
        parameter_template (Optional[ParameterTemplate]): The associated parameter template, if any.
    """

    name: str
    value: str
    on_category: Optional[bool] = False
    parameter_template: Optional[common.models.ParameterTemplate] = None

    def __post_init__(self):
        """Post-initialization to fetch the parameter template if not provided."""
        if not self.parameter_template:
            try:
                self.parameter_template = common.models.ParameterTemplate.objects.get(
                    name__iexact=self.name
                )
            except common.models.ParameterTemplate.DoesNotExist:
                pass


class PartNotFoundError(Exception):
    """Exception raised when a part is not found during import."""


class PartImportError(Exception):
    """Exception raised when an error occurs during part import."""
