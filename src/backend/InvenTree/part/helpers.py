"""Various helper functions for the part app."""

import os

from django.conf import settings

import structlog
from jinja2.sandbox import SandboxedEnvironment

from common.settings import get_global_setting
from InvenTree.cache import get_session_cache, set_session_cache

logger = structlog.get_logger('inventree')


# Compiled template for rendering the 'full_name' attribute of a Part
_part_full_name_template = None
_part_full_name_template_string = ''

# Request cache key for the compiled 'full_name' template
PART_NAME_TEMPLATE_CACHE_KEY = 'part_full_name_template'


class DefaultPartNameTemplate:
    """Fast (non-jinja) renderer for the default 'PART_NAME_FORMAT' template.

    Produces identical output to the default template:
    "{{ part.IPN if part.IPN }}{{ ' | ' if part.IPN }}{{ part.name }}{{ ' | ' if part.revision }}{{ part.revision if part.revision }}"
    """

    def render(self, part) -> str:
        """Render the 'full_name' for the provided part."""
        name = f'{part.IPN} | {part.name}' if part.IPN else str(part.name)

        if part.revision:
            name += f' | {part.revision}'

        return name


def reset_full_name_template(*args, **kwargs):
    """Clear the request-cached 'full_name' template.

    Called when the 'PART_NAME_FORMAT' setting is saved,
    so that the new format is applied within the current request.
    """
    set_session_cache(PART_NAME_TEMPLATE_CACHE_KEY, None)


def compile_full_name_template(*args, **kwargs):
    """Return the compiled template for rendering the 'full_name' attribute of a Part.

    The 'PART_NAME_FORMAT' setting is checked (at most) once per request,
    as this function is called for every Part rendered (e.g. large API list queries).
    The template is only recompiled when the setting value changes.
    """
    global _part_full_name_template
    global _part_full_name_template_string

    if (template := get_session_cache(PART_NAME_TEMPLATE_CACHE_KEY)) is not None:
        return template

    template_string = get_global_setting('PART_NAME_FORMAT', cache=True)

    # Only recompile if the template string has changed
    if (
        template_string != _part_full_name_template_string
        or _part_full_name_template is None
    ):
        from common.setting.system import SYSTEM_SETTINGS

        # Cache the template string
        _part_full_name_template_string = template_string

        if template_string == SYSTEM_SETTINGS['PART_NAME_FORMAT']['default']:
            # Default format - avoid the overhead of jinja rendering
            _part_full_name_template = DefaultPartNameTemplate()
        else:
            env = SandboxedEnvironment(
                variable_start_string='{{', variable_end_string='}}'
            )

            # Compile the template
            try:
                _part_full_name_template = env.from_string(template_string)
            except Exception:
                _part_full_name_template = None

    # Note: An invalid (None) template is not cached, and will be re-checked next call
    set_session_cache(PART_NAME_TEMPLATE_CACHE_KEY, _part_full_name_template)

    return _part_full_name_template


def render_part_full_name(part) -> str:
    """Render the 'full_name' attribute of a Part.

    To improve render efficiency, we re-compile the template whenever the setting is changed

    Args:
        part: The Part object to render
    """
    template = compile_full_name_template()

    if template:
        try:
            return template.render(part=part)
        except Exception as e:
            logger.warning(
                'exception while trying to create full name for part %s: %s',
                part.name,
                e,
            )

    # Fallback to the default format
    elements = [el for el in [part.IPN, part.name, part.revision] if el]
    return ' | '.join(elements)


# Subdirectory for storing part images
PART_IMAGE_DIR = 'part_images'


def get_part_image_directory() -> str:
    """Return the directory where part images are stored.

    Returns:
        str: Directory where part images are stored

    TODO: Future work may be needed here to support other storage backends, such as S3
    """
    part_image_directory = os.path.abspath(
        os.path.join(settings.MEDIA_ROOT, PART_IMAGE_DIR)
    )

    # Create the directory if it does not exist
    if not os.path.exists(part_image_directory):
        os.makedirs(part_image_directory)

    return part_image_directory
