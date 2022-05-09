"""Registry for setups"""
from dataclasses import dataclass
from pathlib import Path

import yaml
import json

from django.conf import settings
from django import forms
from django.utils.translation import gettext_lazy as _

from . import forms as oobe_forms


class SerializableObject():
    def toJson(self):
        """Get JSON compatible representation"""
        return self.__dict__()


@dataclass()
class Page(SerializableObject):
    """Page in a Setup"""
    title: str = ''
    slug: str = ''
    items: dict = None
    is_done: bool = False

    def get_form(self):
        """Returns form for this page - calculated from yaml"""
        # Make sure there are items - return if not
        if not self.items:
            return

        # Base data
        class_name = f'{self.slug}Form'
        form = forms.Form
        attrs = {}

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

            # Add field with uniwue name
            # TODO fix
            if attr_name in attrs:
                attr_name = attr_name + '_'
            attrs[attr_name] = attry_type(**attr_kwargs)

        # Create form and return it
        return type(form)(class_name, (form,), attrs)

    def __dict__(self):
        return {
            'title': self.title,
            'slug': self.slug,
            'is_done': self.is_done,
            'items': self.items,
        }

class PageDict(dict):
    """Collection of Pages"""

    def toJson(self):
        """Returns json-compatible representation of collection"""
        return {key: item.toJson() for key, item in self.items()}


class SetupInstance(SerializableObject):
    """Represents a setup instance"""
    title: str
    """Title of setup"""
    pages: PageDict
    """Collection of all pages as dict (in order of apperance)"""
    form_list: list
    """Formlist fir SetupView (in order of apperance)"""
    done: str
    """Message at the successfull end of the setup"""
    _data: dict = None

    def __init__(self, data: dict, pages: PageDict = None, title: str = None, done: str = None) -> None:
        """Create instance"""
        self.pages = PageDict(pages)
        self.title = title if title else data.get('title')
        self.done = done if done else data.get('done', _('All done here'))
        self._data = data

        # process formlist
        self.form_list = self.get_formlist()

    def __dict__(self, *args, **kwargs):
        data = {
            'title': self.title,
            'done': self.done,
            'pages': self.pages.toJson(),
        }
        return data


    def get_formlist(self):
        """Returns formlist for SetupView"""
        form_list = []
        for item in self.pages.values():
            form = item.get_form()

            # Pages can be just an endpage - so we need to check
            if form:
                form_list.append(form)
        return form_list


class SetupRegistry:
    """Registry for keeping SetupInstance instances"""
    collection: dict[SetupInstance] = {}
    path: list = ['oobe', 'setups']

    def __init__(self) -> None:
        """Creation instance"""
        self.collect()

    def collect(self) -> None:
        """Collects all static setups"""
        new_collection = {}

        # Define base path
        search_path = Path(settings.BASE_DIR).joinpath(*self.path)

        # Iterate over all yaml files
        for item in search_path.glob('**/*.yml'):
            # Load data
            with open(item) as f:
                data = yaml.safe_load(f)

            # Get done text. First check if it is declared - else look at the steps
            done = data.get('done', None)
            pages = data.get('pages', PageDict())
            if not done and pages and len(pages) > 0:
                last_page = list(pages.values())[len(pages) - 1]
                is_done = last_page.get('is_done', None)
                if is_done:
                    done = last_page.get('title', None)

            # Convert pages
            if pages:
                pages = {key: Page(**page, slug=key) for key, page in pages.items()}

            # Add instance
            new_collection[item.stem] = SetupInstance(data, pages=pages, done=done)

        # Save new list
        self.collection = new_collection

    def get(self, key: str, __default) -> SetupInstance:
        """Return SetupInstance of key"""
        return self.collection.get(key, __default)

    def to_representation(self):
        """Returns json-compatible representation of collection"""
        return {key: item.toJson() for key, item in self.collection.items()}


setups = SetupRegistry()
