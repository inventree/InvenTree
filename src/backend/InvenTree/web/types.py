"""Data structures for guides and tipps in InvenTree."""

import dataclasses
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Optional

from django.db.models import QuerySet
from django.utils.functional import Promise
from django.utils.translation import gettext_lazy as _

if TYPE_CHECKING:
    from django.contrib.auth.models import User

    from web.models import GuideDefinition, GuideExecution


@dataclass
class GeneralInfo:
    """General information structure for guides and tipps.

    Attributes:
        title (str): The title of the guide or tipp.
        detail_text (str): Detailed text content.
        links (list[tuple[str, str]]): List of (label, URL) tuples for related links.
        discoverable (bool): Whether this info is discoverable in the user interface / API for non admins.
        permission_cls (Optional[object]): Permission class for access control.
    """

    title: str
    detail_text: str
    links: Optional[list[tuple[str, str]]] = None
    discoverable: bool = True
    permission_cls: Optional[object] = None

    def is_applicable(
        self,
        user: 'User',
        instance: 'GuideDefinition',
        executions: QuerySet['GuideExecution', 'GuideExecution'],
    ) -> bool:
        """Determine if this guide is applicable to the given user.

        This is a base method and should be overridden by subclasses.

        Args:
            user (User): The user to check applicability for.
            instance (GuideDefinition): The guide definition instance.
            executions (QuerySet[GuideExecution]): QuerySet of guide executions for the user.

        Returns:
            bool: True if applicable, False otherwise.
        """
        return True


@dataclass
class Tipp(GeneralInfo):
    """Simple tipp."""

    def is_applicable(self, user, instance, executions) -> bool:
        """Determine if this tipp is applicable to the given user."""
        if not user.is_authenticated:
            return False

        # Tipps are always applicable if not a "done" execution is recorded
        return not executions.filter(done=True).exists()


@dataclass
class FirstUseTipp(GeneralInfo):
    """Tipp - shown only once."""

    per_user: bool = True
    """Only show once per user. If False, show once per installation."""
    show_to_admins: bool = False
    """Whether to show this tipp to all admin users."""

    def is_applicable(self, user, instance, executions) -> bool:
        """Determine if this tipp is applicable to the given user."""
        if not user.is_authenticated:
            return False
        # Placeholder for actual activity check
        return not executions.exists()


@dataclass
class GuideDefinitionData:
    """Data structure for guide definition data.

    Initiate a object of this class to define a guide definition. This will be discovered during startup, registered and made concrete in the database.

    Attributes:
        name (str): The name of the guide.
        slug (str): The URL-friendly unique identifier for the guide.
        description (str): Optional description of the guide.
        setup (Union[Tipp, FirstUseTipp, Guide]): The functional data for the guide, which can be any of the defined types.
    """

    name: str
    slug: str
    setup: Tipp | FirstUseTipp
    description: str = ''

    @property
    def guide_type(self) -> str:
        """Determine the guide type based on the setup instance."""
        if isinstance(self.setup, Tipp):
            return 'tipp'
        elif isinstance(self.setup, FirstUseTipp):
            return 'firstuse'
        else:
            raise ValueError('Invalid setup type for GuideDefinitionData')

    @property
    def data(self) -> dict[str, Any]:
        """Return the data as a dictionary suitable for JSONField storage."""
        _data = dataclasses.asdict(self.setup)
        # Transform proxy objects into json friendly data
        for key, value in _data.items():
            if isinstance(value, Promise):
                _data[key] = str(value)
        return _data

    def set_db(self, obj):
        """Set the linked database object."""
        self._db_obj = obj


# Real guides
guides = [
    GuideDefinitionData(
        name='Admin Center Information Release Info',
        slug='admin_center_1',
        setup=Tipp(
            title=_('Admin Center Information'),
            detail_text=_(
                'The home panel (and the whole Admin Center) is a new feature starting with the new UI and was previously (before 1.0) not available.\n'
                'The admin center provides a centralized location for all administration functionality and is meant to replace all interaction with the (django) backend admin interface.\n'
                'Please open feature requests (after checking the tracker) for any existing backend admin functionality you are missing in this UI. The backend admin interface should be used carefully and seldom.'
            ),
        ),
    )
]
