"""Configuration options for django-markdownify.

Ref: https://django-markdownify.readthedocs.io/en/latest/settings.html
"""


def markdownify_config():
    """Return configuration dictionary for django-markdownify."""
    return {
        'default': {
            'BLEACH': True,
            'WHITELIST_ATTRS': ['href', 'src', 'alt'],
            'MARKDOWN_EXTENSIONS': ['markdown.extensions.extra'],
            'WHITELIST_TAGS': [
                'a',
                'abbr',
                'b',
                'blockquote',
                'code',
                'em',
                'h1',
                'h2',
                'h3',
                'h4',
                'h5',
                'hr',
                'i',
                'img',
                'li',
                'ol',
                'p',
                'pre',
                's',
                'strong',
                'table',
                'thead',
                'tbody',
                'th',
                'tr',
                'td',
                'ul',
            ],
        }
    }
