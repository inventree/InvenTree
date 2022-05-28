"""Custom management command to prerender files."""

import os

from django.conf import settings
from django.core.management.base import BaseCommand
from django.http.request import HttpRequest
from django.template.loader import render_to_string
from django.utils.module_loading import import_string
from django.utils.translation import override as lang_over


def render_file(file_name, source, target, locales, ctx):
    """Renders a file into all provided locales."""
    for locale in locales:
        target_file = os.path.join(target, locale + '.' + file_name)
        with open(target_file, 'w') as localised_file:
            with lang_over(locale):
                renderd = render_to_string(os.path.join(source, file_name), ctx)
                localised_file.write(renderd)


class Command(BaseCommand):
    """Django command to prerender files."""

    def handle(self, *args, **kwargs):
        # static directories
        LC_DIR = settings.LOCALE_PATHS[0]
        SOURCE_DIR = settings.STATICFILES_I18_SRC
        TARGET_DIR = settings.STATICFILES_I18_TRG

        # ensure static directory exists
        if not os.path.exists(TARGET_DIR):
            os.makedirs(TARGET_DIR, exist_ok=True)

        # collect locales
        locales = {}
        for locale in os.listdir(LC_DIR):
            path = os.path.join(LC_DIR, locale)
            if os.path.exists(path) and os.path.isdir(path):
                locales[locale] = locale

        # render!
        request = HttpRequest()
        ctx = {}
        processors = tuple(import_string(path) for path in settings.STATFILES_I18_PROCESSORS)
        for processor in processors:
            ctx.update(processor(request))

        for file in os.listdir(SOURCE_DIR, ):
            path = os.path.join(SOURCE_DIR, file)
            if os.path.exists(path) and os.path.isfile(path):
                print(f"render {file}")
                render_file(file, SOURCE_DIR, TARGET_DIR, locales, ctx)
            else:
                raise NotImplementedError('Using multi-level directories is not implemented at this point')  # TODO multilevel dir if needed
        print(f"rendered all files in {SOURCE_DIR}")
