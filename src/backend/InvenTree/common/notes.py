"""Built-in formats for note source content."""

import copy
import json
import re

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

import nh3


class NoteContentType(models.TextChoices):
    """Supported storage formats for notes."""

    HTML = 'text/html', _('HTML')
    JSON = 'application/json', _('JSON')
    PLAIN_TEXT = 'text/plain', _('Plain text')


class RawNoteContent:
    """Raw note content with literal display and no embedded-image support."""

    supports_images = False

    @staticmethod
    def clean(content: str) -> str:
        """Return the source text unchanged."""
        return content

    @staticmethod
    def render(content: str) -> str:
        """Escape source text for use in reports."""
        return format_html(
            '<pre style="white-space: pre-wrap; overflow-wrap: anywhere">{}</pre>',
            content,
        )


class JsonNoteContent(RawNoteContent):
    """JSON note content validated without reformatting."""

    @staticmethod
    def clean(content: str) -> str:
        """Reject invalid JSON, including nonstandard numeric constants."""

        def reject_constant(value):
            raise ValueError(f'Invalid JSON constant: {value}')

        try:
            json.loads(content, parse_constant=reject_constant)
        except RecursionError as exc:
            raise ValidationError({'content': _('JSON is nested too deeply.')}) from exc
        except ValueError as exc:
            raise ValidationError({
                'content': _('Invalid JSON: %(error)s') % {'error': str(exc)}
            }) from exc
        return content


class HtmlNoteContent:
    """Sanitized HTML note content with embedded-image support."""

    supports_images = True

    @staticmethod
    def clean(content: str) -> str:
        """Return sanitized HTML with permitted styles and image attributes."""
        if content:
            attrs = copy.deepcopy(nh3.ALLOWED_ATTRIBUTES)

            for tag in (
                'span',
                'p',
                'div',
                'img',
                'a',
                'h1',
                'h2',
                'h3',
                'h4',
                'h5',
                'h6',
                'ul',
                'ol',
                'li',
                'blockquote',
                'pre',
                'table',
                'thead',
                'tbody',
                'tr',
                'td',
                'th',
                'colgroup',
                'col',
            ):
                attrs.setdefault(tag, set()).update({'style'})

            # Allow class on structural tags used by the rich-text editor
            for tag in ('div', 'span', 'img', 'table', 'td', 'th', 'col'):
                attrs.setdefault(tag, set()).add('class')

            # Allow image attributes used by tiptap-extension-resizable-image
            attrs.setdefault('img', set()).update({'data-keep-ratio', 'colwidth'})

            content = nh3.clean(
                content.strip(),
                attributes=attrs,
                filter_style_properties={
                    'color',
                    'background-color',
                    'font-size',
                    'font-weight',
                    'font-style',
                    'font-family',
                    'text-decoration',
                    'text-align',
                    'border',
                    'border-color',
                    'border-style',
                    'border-width',
                    'margin',
                    'padding',
                    'column-width',
                    'column-height',
                    'min-width',
                    'max-width',
                    'min-height',
                    'max-height',
                    'width',
                    'height',
                },
            )

            # nh3 does not recognise legacy IE-only CSS expression() calls as
            # unsafe, so they survive style attribute filtering - strip them explicitly
            content = re.sub(r'expression\s*\(', '', content, flags=re.IGNORECASE)

        return content


NOTE_CONTENT_HANDLERS = {
    NoteContentType.HTML: HtmlNoteContent,
    NoteContentType.JSON: JsonNoteContent,
    NoteContentType.PLAIN_TEXT: RawNoteContent,
}


def note_content_handler(content_type: str):
    """Return the content handler for a supported MIME type."""
    try:
        return NOTE_CONTENT_HANDLERS[content_type]
    except KeyError as exc:
        raise ValidationError({
            'content_type': _('Unsupported note content type')
        }) from exc
