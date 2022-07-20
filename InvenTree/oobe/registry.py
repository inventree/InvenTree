"""Registry for setups."""

from dataclasses import dataclass
from pathlib import Path
from typing import List

from django import forms
from django.conf import settings
from django.utils.translation import gettext_lazy as _

import yaml

from . import forms as oobe_forms


@dataclass()
class Page():
    """Page in a Setup."""
    title: str = ''
    slug: str = ''
    items: dict = None
    is_done: bool = False

    def get_form(self):
        """Returns form for this page - calculated from yaml."""
        # Make sure there are items - return if not
        if not self.items:
            return

        # Base data
        class_name = f'{self.slug}Form'
        form = forms.Form
        attrs = {}

        # helper function
        def unique_name(reference):
            """Ensure name is unique."""
            if reference in attrs:
                reference = reference + '_'
                return unique_name(reference)
            return reference

        # Set up fields
        for item in self.items:
            # Set field name
            attr_name = list(item.keys())[0]

            # Standard values
            attry_type = forms.CharField
            attr_kwargs = {}

            # Select type
            if attr_name == 'char':
                attry_type = forms.CharField
            elif attr_name == 'text':
                attry_type = forms.CharField
                attr_kwargs = {
                    'widget': forms.Textarea,
                }
            elif attr_name == 'email':
                attry_type = forms.EmailField
            elif attr_name == 'int':
                attry_type = forms.IntegerField
            elif attr_name == 'info':
                attry_type = forms.CharField
                attr_kwargs = {
                    'widget': oobe_forms.CommentTextWidget,
                    'required': False,
                    'label': list(item.values())[0]
                }

            # Add field with unique name
            attr_name = unique_name(attr_name)
            attrs[attr_name] = attry_type(**attr_kwargs)

        # Create form and return it
        return type(form)(class_name, (form,), attrs)

    def toJson(self):
        """Get JSON compatible representation."""
        return {
            'title': self.title,
            'slug': self.slug,
            'is_done': self.is_done,
            'items': self.items,
        }


class PageDict(dict):
    """Collection of Pages."""

    def toJson(self):
        """Returns json-compatible representation of collection."""
        return {key: item.toJson() for key, item in self.items()}


class SetupInstance():
    """Represents a setup instance."""

    title: str
    """Title of setup"""
    pages: PageDict
    """Collection of all pages as dict (in order of apperance)"""
    form_list: list
    """Formlist fir SetupView (in order of apperance)"""
    done: str
    """Message at the successfull end of the setup"""
    done_function: str
    """Reference to the function that should be called when the setup is done."""
    _data: dict = None

    def __init__(self, data: dict, pages: PageDict = None, title: str = None, done: str = None, done_function: str = None) -> None:
        """Create instance.

        Args:
            data (dict): Data for setup.
            pages (PageDict, optional): All contained pages. Defaults to None.
            title (str, optional): Title for renderings. Defaults to None.
            done (str, optional): Title of the final step once the setup is done. Defaults to All done here.
            done_function (str, optional): Action to take once the setup is done. Defaults to None.
        """
        self.pages = PageDict(pages)
        self.title = title if title else data.get('title')
        self.done = done if done else data.get('done', _('All done here'))
        self.done_function = done_function if done_function else data.get('done_function', None)
        self._data = data

        # process formlist
        self.form_list = self.get_formlist()

    def toJson(self):
        """Get JSON compatible representation."""
        return {
            'title': self.title,
            'done': self.done,
            'pages': self.pages.toJson(),
        }

    def get_formlist(self):
        """Returns formlist for SetupView."""
        form_list = []
        for item in self.pages.values():
            form = item.get_form()

            # Pages can be just an endpage - so we need to check
            if form:
                form_list.append((item.slug, form))
        return tuple(form_list)


class SetupRegistry:
    """Registry for keeping SetupInstance instances."""
    collection: List[SetupInstance] = {}
    path: list = ['oobe', 'templates', 'setups']
    valid_versions: list = [1, ]

    def __init__(self) -> None:
        """Creation instance."""
        self.collect()

    def collect(self) -> None:
        """Collects all static setups."""
        new_collection = {}

        # Define base path
        search_path = Path(settings.BASE_DIR).joinpath(*self.path)

        # Iterate over all yaml files
        for item in search_path.glob('**/*.yml'):
            # Load data
            with open(item) as f:
                data = yaml.safe_load(f)

            # Check if it is a setup
            if not data.get('inventree_setup', False):
                continue

            # Check if the template has a valid version
            if data.get('version', None) not in self.valid_versions:
                continue

            # Get done text. First check if it is declared - else look at the steps
            done = data.get('done', None)
            done_function = None
            pages = data.get('pages', PageDict())
            if not done and pages and len(pages) > 0:
                last_page = list(pages.values())[len(pages) - 1]
                is_done = last_page.get('is_done', None)
                if is_done:
                    done = last_page.get('title', None)
                    done_function = is_done

            # Convert pages
            if pages:
                pages = {key: Page(**page, slug=key) for key, page in pages.items()}

            # Instance reference
            reference = data.get('slug', None)
            reference = item.stem if not reference else reference

            # Add instance
            new_collection[reference] = SetupInstance(data, pages=pages, done=done, done_function=done_function)

        # Save new list
        self.collection = new_collection

    def get(self, key: str, __default=None) -> SetupInstance:
        """Return SetupInstance of key."""
        return self.collection.get(key, __default)

    def to_representation(self):
        """Returns json-compatible representation of collection."""
        return {key: item.toJson() for key, item in self.collection.items()}


setups = SetupRegistry()
