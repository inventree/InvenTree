"""Various helper functions for the part app."""

import logging
import os

from django.conf import settings

from jinja2 import Environment, select_autoescape

logger = logging.getLogger('inventree')


# Compiled template for rendering the 'full_name' attribute of a Part
_part_full_name_template = None
_part_full_name_template_string = ''


def compile_full_name_template(*args, **kwargs):
    """Recompile the template for rendering the 'full_name' attribute of a Part.

    This function is called whenever the 'PART_NAME_FORMAT' setting is changed.
    """
    from common.models import InvenTreeSetting

    global _part_full_name_template
    global _part_full_name_template_string

    template_string = InvenTreeSetting.get_setting('PART_NAME_FORMAT', '')

    # Skip if the template string has not changed
    if (
        template_string == _part_full_name_template_string
        and _part_full_name_template is not None
    ):
        return _part_full_name_template

    # Cache the template string
    _part_full_name_template_string = template_string

    env = Environment(
        autoescape=select_autoescape(default_for_string=False, default=False),
        variable_start_string='{{',
        variable_end_string='}}',
    )

    # Compile the template
    try:
        _part_full_name_template = env.from_string(template_string)
    except Exception:
        _part_full_name_template = None

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
