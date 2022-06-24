"""This module provides custom translation tags specifically for use with javascript code.

Translated strings are escaped, such that they can be used as string literals in a javascript file.
"""

import django.templatetags.i18n
from django import template
from django.template import TemplateSyntaxError
from django.templatetags.i18n import TranslateNode

register = template.Library()


class CustomTranslateNode(TranslateNode):
    """Custom translation node class, which sanitizes the translated strings for javascript use"""

    def render(self, context):
        """Custom render function overrides / extends default behaviour"""

        result = super().render(context)

        return result


@register.tag("translate")
@register.tag("trans")
def do_translate(parser, token):
    """Custom translation function, lifted from https://github.com/django/django/blob/main/django/templatetags/i18n.py

    The only difference is that we pass this to our custom rendering node class
    """

    bits = token.split_contents()
    if len(bits) < 2:
        raise TemplateSyntaxError("'%s' takes at least one argument" % bits[0])
    message_string = parser.compile_filter(bits[1])
    remaining = bits[2:]

    noop = False
    asvar = None
    message_context = None
    seen = set()
    invalid_context = {"as", "noop"}

    while remaining:
        option = remaining.pop(0)
        if option in seen:
            raise TemplateSyntaxError(
                "The '%s' option was specified more than once." % option,
            )
        elif option == "noop":
            noop = True
        elif option == "context":
            try:
                value = remaining.pop(0)
            except IndexError:
                raise TemplateSyntaxError(
                    "No argument provided to the '%s' tag for the context option."
                    % bits[0]
                )
            if value in invalid_context:
                raise TemplateSyntaxError(
                    "Invalid argument '%s' provided to the '%s' tag for the context "
                    "option" % (value, bits[0]),
                )
            message_context = parser.compile_filter(value)
        elif option == "as":
            try:
                value = remaining.pop(0)
            except IndexError:
                raise TemplateSyntaxError(
                    "No argument provided to the '%s' tag for the as option." % bits[0]
                )
            asvar = value
        else:
            raise TemplateSyntaxError(
                "Unknown argument for '%s' tag: '%s'. The only options "
                "available are 'noop', 'context' \"xxx\", and 'as VAR'."
                % (
                    bits[0],
                    option,
                )
            )
        seen.add(option)

    return CustomTranslateNode(message_string, noop, asvar, message_context)


# Re-register tags which we have not explicitly overridden
register.tag("blocktrans", django.templatetags.i18n.do_block_translate)
register.tag("blocktranslate", django.templatetags.i18n.do_block_translate)

register.tag("language", django.templatetags.i18n.language)

register.tag("get_available_languages", django.templatetags.i18n.do_get_available_languages)
register.tag("get_language_info", django.templatetags.i18n.do_get_language_info)
register.tag("get_language_info_list", django.templatetags.i18n.do_get_language_info_list)
register.tag("get_current_language", django.templatetags.i18n.do_get_current_language)
register.tag("get_current_language_bidi", django.templatetags.i18n.do_get_current_language_bidi)

register.filter("language_name", django.templatetags.i18n.language_name)
register.filter("language_name_translated", django.templatetags.i18n.language_name_translated)
register.filter("language_name_local", django.templatetags.i18n.language_name_local)
register.filter("language_bidi", django.templatetags.i18n.language_bidi)
