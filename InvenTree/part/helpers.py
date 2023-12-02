"""Various helper functions for the part app"""

import logging

from jinja2 import Environment

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
    if template_string == _part_full_name_template_string and _part_full_name_template is not None:
        return _part_full_name_template

    _part_full_name_template_string = template_string

    # skipqc: BAN-B701
    env = Environment(
        autoescape=False,
        variable_start_string='{{',
        variable_end_string='}}'
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
            logger.warning("exception while trying to create full name for part %s: %s", part.name, e)

    # Fallback to the default format
    elements = [el for el in [part.IPN, part.name, part.revision] if el]
    return ' | '.join(elements)
