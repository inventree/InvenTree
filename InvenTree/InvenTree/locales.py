"""Support translation locales for InvenTree.

If a new language translation is supported, it must be added here
After adding a new language, run the following command:
python manage.py makemessages -l <language_code> -e html,js,py --no-wrap
where <language_code> is the code for the new language
Additionally, update the /src/frontend/.linguirc file
"""

from django.utils.translation import gettext_lazy as _

LOCALES = [
    ('bg', _('Bulgarian')),
    ('cs', _('Czech')),
    ('da', _('Danish')),
    ('de', _('German')),
    ('el', _('Greek')),
    ('en', _('English')),
    ('es', _('Spanish')),
    ('es-mx', _('Spanish (Mexican)')),
    ('fa', _('Farsi / Persian')),
    ('fi', _('Finnish')),
    ('fr', _('French')),
    ('he', _('Hebrew')),
    ('hi', _('Hindi')),
    ('hu', _('Hungarian')),
    ('it', _('Italian')),
    ('ja', _('Japanese')),
    ('ko', _('Korean')),
    ('nl', _('Dutch')),
    ('no', _('Norwegian')),
    ('pl', _('Polish')),
    ('pt', _('Portuguese')),
    ('pt-br', _('Portuguese (Brazilian)')),
    ('ru', _('Russian')),
    ('sl', _('Slovenian')),
    ('sr', _('Serbian')),
    ('sv', _('Swedish')),
    ('th', _('Thai')),
    ('tr', _('Turkish')),
    ('vi', _('Vietnamese')),
    ('zh-hans', _('Chinese (Simplified)')),
    ('zh-hant', _('Chinese (Traditional)')),
]
