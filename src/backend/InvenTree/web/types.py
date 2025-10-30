"""Data structures for guides and tipps in InvenTree."""

from dataclasses import dataclass
from typing import Optional, Union

from django.utils.translation import gettext_lazy as _


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
    links: list[tuple[str, str]]
    discoverable: bool = True
    permission_cls: Optional[object] = None


@dataclass
class Tipp(GeneralInfo):
    """Simple tipp."""


@dataclass
class FirstUseTipp(GeneralInfo):
    """Tipp - shown only once."""

    per_user: bool = True
    """Only show once per user. If False, show once per installation."""
    show_to_admins: bool = False
    """Whether to show this tipp to all admin users."""


@dataclass
class GuideStep:
    """Single step within a guide.

    Attributes:
        order_number (int): The execution order number of the step.
        title (str): The title of the step.
        detail_text (str): Detailed text content for the step.
        links (list[tuple[str, str]]): List of (label, URL) tuples for related links.
        btn_next_text (str): Text label for the 'next' button.
        btn_back_text (str): Text label for the 'back' button.
        style(str): Style of the step (e.g., 'normal', 'highlighted').
        picture (Optional[str]): URL or path to a picture that should be shown.
        action_text (Optional[str]): Text label for the action button, if applicable.
        fnc_action (Optional[object]): Optional function to execute as an action for this step.
        fnc_before (Optional[object]): Optional function to execute before this step.
        fnc_after (Optional[object]): Optional function to execute after this step.
    """

    order_number: int
    # General content
    title: str
    detail_text: str
    links: list[tuple[str, str]]
    # UI interactions
    btn_next_text: str = _('Next')
    btn_back_text: str = _('Back')
    style: str = 'normal'
    picture: Optional[str] = None
    """URL or path to a picture that should be shown."""
    # Things that cause actions
    action_text: Optional[str] = None
    fnc_action: Optional[object] = None
    fnc_before: Optional[object] = None
    fnc_after: Optional[object] = None


@dataclass
class Guide(GeneralInfo):
    """(Multi)step guide."""

    steps: list[GuideStep]
    show_total_steps: bool = True
    """Whether to show total steps in the UI."""
    calculate_next_step: Optional[object] = None
    """Optional function to calculate the next step dynamically."""
    btn_final_text: str = _('Finish')
    """Text label for the final (last) button."""


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
    description: str
    setup: Union[Tipp, FirstUseTipp, Guide]

    @property
    def guide_type(self) -> str:
        """Determine the guide type based on the setup instance."""
        if isinstance(self.setup, Tipp):
            return 'tipp'
        elif isinstance(self.setup, FirstUseTipp):
            return 'firstuse'
        elif isinstance(self.setup, Guide):
            return 'guide'
        else:
            raise ValueError('Invalid setup type for GuideDefinitionData')
