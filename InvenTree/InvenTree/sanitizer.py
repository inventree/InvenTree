"""Functions to sanitize user input files."""
from bleach import clean
from bleach.css_sanitizer import CSSSanitizer

ALLOWED_ELEMENTS_SVG = [
    'a', 'animate', 'animateColor', 'animateMotion',
    'animateTransform', 'circle', 'defs', 'desc', 'ellipse', 'font-face',
    'font-face-name', 'font-face-src', 'g', 'glyph', 'hkern',
    'linearGradient', 'line', 'marker', 'metadata', 'missing-glyph',
    'mpath', 'path', 'polygon', 'polyline', 'radialGradient', 'rect',
    'set', 'stop', 'svg', 'switch', 'text', 'title', 'tspan', 'use'
]

ALLOWED_ATTRIBUTES_SVG = [
    'accent-height', 'accumulate', 'additive', 'alphabetic',
    'arabic-form', 'ascent', 'attributeName', 'attributeType',
    'baseProfile', 'bbox', 'begin', 'by', 'calcMode', 'cap-height',
    'class', 'color', 'color-rendering', 'content', 'cx', 'cy', 'd', 'dx',
    'dy', 'descent', 'display', 'dur', 'end', 'fill', 'fill-opacity',
    'fill-rule', 'font-family', 'font-size', 'font-stretch', 'font-style',
    'font-variant', 'font-weight', 'from', 'fx', 'fy', 'g1', 'g2',
    'glyph-name', 'gradientUnits', 'hanging', 'height', 'horiz-adv-x',
    'horiz-origin-x', 'id', 'ideographic', 'k', 'keyPoints',
    'keySplines', 'keyTimes', 'lang', 'marker-end', 'marker-mid',
    'marker-start', 'markerHeight', 'markerUnits', 'markerWidth',
    'mathematical', 'max', 'min', 'name', 'offset', 'opacity', 'orient',
    'origin', 'overline-position', 'overline-thickness', 'panose-1',
    'path', 'pathLength', 'points', 'preserveAspectRatio', 'r', 'refX',
    'refY', 'repeatCount', 'repeatDur', 'requiredExtensions',
    'requiredFeatures', 'restart', 'rotate', 'rx', 'ry', 'slope',
    'stemh', 'stemv', 'stop-color', 'stop-opacity',
    'strikethrough-position', 'strikethrough-thickness', 'stroke',
    'stroke-dasharray', 'stroke-dashoffset', 'stroke-linecap',
    'stroke-linejoin', 'stroke-miterlimit', 'stroke-opacity',
    'stroke-width', 'systemLanguage', 'target', 'text-anchor', 'to',
    'transform', 'type', 'u1', 'u2', 'underline-position',
    'underline-thickness', 'unicode', 'unicode-range', 'units-per-em',
    'values', 'version', 'viewBox', 'visibility', 'width', 'widths', 'x',
    'x-height', 'x1', 'x2', 'xlink:actuate', 'xlink:arcrole',
    'xlink:href', 'xlink:role', 'xlink:show', 'xlink:title',
    'xlink:type', 'xml:base', 'xml:lang', 'xml:space', 'xmlns',
    'xmlns:xlink', 'y', 'y1', 'y2', 'zoomAndPan', 'style'
]


def sanitize_svg(file_data: str, strip: bool = True, elements: str = ALLOWED_ELEMENTS_SVG, attributes: str = ALLOWED_ATTRIBUTES_SVG) -> str:
    """Sanatize a SVG file.

    Args:
        file_data (str): SVG as string.
        strip (bool, optional): Should invalid elements get removed. Defaults to True.
        elements (str, optional): Allowed elements. Defaults to ALLOWED_ELEMENTS_SVG.
        attributes (str, optional): Allowed attributes. Defaults to ALLOWED_ATTRIBUTES_SVG.

    Returns:
        str: Sanitzied SVG file.
    """

    cleaned = clean(
        file_data,
        tags=elements,
        attributes=attributes,
        strip=strip,
        strip_comments=strip,
        css_sanitizer=CSSSanitizer()
    )
    return cleaned
