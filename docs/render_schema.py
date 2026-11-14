"""Render sections of the InvenTree OpenAPI schema as static Markdown pages.

This replaces the 'neoteroi.mkdocsoad' plugin, so that the API documentation
is plain Markdown which can be rendered by any static site generator
(mkdocs, zensical, etc), without requiring a build-time plugin.

The rendered pages are generated as a pre-build step (see 'extract_schema.py').
"""

import json
import re
from typing import Any, Optional

HTTP_METHODS = ['get', 'post', 'put', 'patch', 'delete', 'head', 'options']

# Placeholder values for generated examples, keyed by OpenAPI 'format'
FORMAT_EXAMPLES = {
    'date': '2024-01-01',
    'date-time': '2024-01-01T12:00:00Z',
    'time': '12:00:00',
    'email': 'user@example.com',
    'uri': 'https://example.com',
    'uuid': '3fa85f64-5717-4562-b3fc-2c963f66afa6',
    'decimal': '0.00',
    'binary': '<binary>',
    'ipv4': '127.0.0.1',
}

# Maximum depth when generating JSON examples (guards against deep nesting)
EXAMPLE_MAX_DEPTH = 5


def schema_anchor(name: str) -> str:
    """Return the HTML anchor for a named component schema."""
    return 'schema-' + re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')


def operation_anchor(method: str, path: str) -> str:
    """Return the HTML anchor for a single API operation."""
    return method.lower() + '-' + re.sub(r'[^a-z0-9]+', '-', path.lower()).strip('-')


def escape_text(text: Any) -> str:
    """Escape free text so it cannot inject HTML into the rendered page.

    Markdown formatting (e.g. `code` or *emphasis*) is preserved.
    """
    text = '' if text is None else str(text)
    return text.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')


def escape_cell(text: Any) -> str:
    """Escape text for use within a single Markdown table cell."""
    text = escape_text(text).strip()
    text = text.replace('|', '\\|')

    lines = []

    for line in text.splitlines():
        line = line.strip()
        # Bulleted lists cannot be rendered within a table cell
        if line.startswith(('* ', '- ')):
            line = '• ' + line[2:]
        lines.append(line)

    return '<br>'.join(line for line in lines if line)


def inline_code(text: Any) -> str:
    """Wrap a value as inline code, coping with embedded backticks."""
    text = str(text)
    fence = '``' if '`' in text else '`'
    pad = ' ' if '`' in text else ''
    return f'{fence}{pad}{text}{pad}{fence}'


class SchemaRenderer:
    """Render API operations and their component schemas to Markdown."""

    def __init__(self, spec: dict):
        """Initialize the renderer with the *complete* OpenAPI spec.

        The full spec is required so that '$ref' entries can always be resolved,
        regardless of which subset of paths is being rendered.
        """
        self.spec = spec
        self.components = spec.get('components', {})
        self.schemas = self.components.get('schemas', {})

    # ------------------------------------------------------------------ #
    # Reference handling
    # ------------------------------------------------------------------ #

    @staticmethod
    def ref_name(ref: str) -> str:
        """Return the final component name from a '$ref' string."""
        return ref.split('/')[-1]

    def resolve(self, obj: Any) -> Any:
        """Resolve a '$ref' (to any component type) into the referenced object."""
        seen = set()

        while isinstance(obj, dict) and '$ref' in obj:
            ref = obj['$ref']

            if ref in seen or not ref.startswith('#/'):
                break

            seen.add(ref)
            node = self.spec

            for part in ref[2:].split('/'):
                node = node.get(part, {}) if isinstance(node, dict) else {}

            obj = node

        return obj

    def collect_schema_refs(self, obj: Any, found: Optional[set] = None) -> set:
        """Find all component schemas referenced (transitively) by an object.

        References to other component types (e.g. responses or parameters)
        are followed, so that the schemas they use are also included.
        """
        found = set() if found is None else found
        stack = [obj]
        visited = set()

        while stack:
            node = stack.pop()

            if isinstance(node, list):
                stack.extend(node)
                continue

            if not isinstance(node, dict):
                continue

            ref = node.get('$ref')

            if isinstance(ref, str) and ref not in visited:
                visited.add(ref)

                if ref.startswith('#/components/schemas/'):
                    found.add(self.ref_name(ref))

                stack.append(self.resolve(node))

            stack.extend(v for k, v in node.items() if k != '$ref')

        return found

    # ------------------------------------------------------------------ #
    # Type descriptions
    # ------------------------------------------------------------------ #

    def type_str(self, schema: Any) -> str:
        """Return a short (Markdown) description of a schema's type."""
        if not isinstance(schema, dict):
            return ''

        if '$ref' in schema:
            ref = schema['$ref']

            if ref.startswith('#/components/schemas/'):
                name = self.ref_name(ref)
                return f'[{name}](#{schema_anchor(name)})'

            return self.type_str(self.resolve(schema))

        for key, joiner in (('allOf', ' & '), ('oneOf', ' or '), ('anyOf', ' or ')):
            if key in schema:
                options = [self.type_str(s) for s in schema[key]]
                return joiner.join(o for o in options if o) or 'any'

        schema_type = schema.get('type')

        if schema_type == 'array':
            return f'array[{self.type_str(schema.get("items", {})) or "any"}]'

        if schema_type == 'object' or (not schema_type and 'properties' in schema):
            extra = schema.get('additionalProperties')

            if isinstance(extra, dict) and extra:
                return f'object[string, {self.type_str(extra) or "any"}]'

            return 'object'

        if not schema_type:
            return 'any'

        if fmt := schema.get('format'):
            return f'{schema_type}({fmt})'

        return schema_type

    def merged(self, schema: dict) -> dict:
        """Flatten 'allOf' wrappers so that flags such as 'readOnly' are visible."""
        if not isinstance(schema, dict):
            return {}

        result = {k: v for k, v in schema.items() if k != 'allOf'}

        for sub in schema.get('allOf', []):
            sub = self.resolve(sub)
            if isinstance(sub, dict):
                for k, v in sub.items():
                    result.setdefault(k, v)

        return result

    def constraints(self, schema: dict, description: str = '') -> list[str]:
        """Return a list of human readable constraints for a schema.

        Arguments:
            schema: The schema to describe
            description: Accompanying description text. Enum values are not
                repeated if the description already lists them all.
        """
        notes = []

        enum_listed = all(
            f'`{v}`' in (description or '') for v in schema.get('enum', []) if v
        )

        if 'enum' in schema and not enum_listed:
            values = ', '.join(inline_code(json.dumps(v)) for v in schema['enum'])
            notes.append(f'One of: {values}')

        for key, label in (
            ('minLength', 'Min length'),
            ('maxLength', 'Max length'),
            ('minimum', 'Minimum'),
            ('maximum', 'Maximum'),
            ('minItems', 'Min items'),
            ('maxItems', 'Max items'),
        ):
            if key in schema:
                notes.append(f'{label}: {inline_code(schema[key])}')

        if 'pattern' in schema:
            notes.append(f'Pattern: {inline_code(schema["pattern"])}')

        if 'default' in schema:
            notes.append(f'Default: {inline_code(json.dumps(schema["default"]))}')

        return notes

    # ------------------------------------------------------------------ #
    # Example generation
    # ------------------------------------------------------------------ #

    def example(
        self, schema: Any, mode: str = 'response', depth: int = 0, stack=()
    ) -> Any:
        """Generate an example value for a schema.

        Arguments:
            schema: The schema to generate an example for
            mode: 'request' (omit read-only fields) or 'response' (omit write-only fields)
            depth: Current nesting depth
            stack: Component names currently being expanded (cycle protection)
        """
        if not isinstance(schema, dict) or depth > EXAMPLE_MAX_DEPTH:
            return None

        if '$ref' in schema:
            name = self.ref_name(schema['$ref'])

            if name in stack:
                return {}

            return self.example(self.resolve(schema), mode, depth, (*stack, name))

        if 'example' in schema:
            return schema['example']

        if 'allOf' in schema:
            result = {}
            for sub in schema['allOf']:
                value = self.example(sub, mode, depth, stack)
                if isinstance(value, dict):
                    result.update(value)
                elif value is not None:
                    return value
            return result

        for key in ('oneOf', 'anyOf'):
            if key in schema:
                # Prefer the first option which is not a 'null' or 'blank' variant
                for sub in schema[key]:
                    value = self.example(sub, mode, depth, stack)
                    if value not in (None, ''):
                        return value
                return None

        if 'default' in schema:
            return schema['default']

        if 'enum' in schema:
            options = [v for v in schema['enum'] if v not in (None, '')]
            return options[0] if options else None

        schema_type = schema.get('type')

        if schema_type == 'object' or 'properties' in schema:
            result = {}

            for name, prop in schema.get('properties', {}).items():
                flags = self.merged(prop)
                if mode == 'request' and flags.get('readOnly'):
                    continue
                if mode == 'response' and flags.get('writeOnly'):
                    continue
                result[name] = self.example(prop, mode, depth + 1, stack)

            return result

        if schema_type == 'array':
            item = self.example(schema.get('items', {}), mode, depth + 1, stack)
            return [] if item is None else [item]

        if schema_type == 'string':
            return FORMAT_EXAMPLES.get(schema.get('format'), 'string')

        if schema_type == 'integer':
            return 0

        if schema_type == 'number':
            return 0.0

        if schema_type == 'boolean':
            return False

        return None

    def example_block(self, schema: dict, mode: str, title: str) -> list[str]:
        """Render a collapsible JSON example for the given schema."""
        value = self.example(schema, mode)

        if value is None:
            return []

        body = json.dumps(value, indent=2)

        lines = [f'??? example "{title}"', '    ```json']
        lines += ['    ' + line for line in body.splitlines()]
        lines += ['    ```', '']

        return lines

    # ------------------------------------------------------------------ #
    # Operations
    # ------------------------------------------------------------------ #

    @staticmethod
    def security_names(security: Optional[list]) -> tuple:
        """Return a sorted tuple of security scheme names for an operation."""
        if not security:
            return ()

        names = set()

        for requirement in security:
            names.update(requirement.keys())

        return tuple(sorted(names))

    def render_security(self, names: tuple) -> str:
        """Render a list of security schemes as Markdown."""
        if not names:
            return 'No authentication required'

        return ', '.join(inline_code(n) for n in names)

    def render_parameters(self, parameters: list) -> list[str]:
        """Render the parameters of an operation as a table."""
        if not parameters:
            return []

        lines = [
            '**Parameters**',
            '',
            '| Name | In | Type | Required | Description |',
            '| --- | --- | --- | --- | --- |',
        ]

        for param in parameters:
            param = self.resolve(param)
            schema = param.get('schema', {})
            notes = [escape_cell(param.get('description', ''))]
            notes += self.constraints(
                self.merged(self.resolve(schema)), param.get('description', '')
            )
            description = '<br>'.join(n for n in notes if n)

            lines.append(
                f'| {inline_code(param.get("name", ""))} '
                f'| {param.get("in", "")} '
                f'| {self.type_str(schema)} '
                f'| {"Yes" if param.get("required") else "No"} '
                f'| {description} |'
            )

        return [*lines, '']

    def render_request_body(self, body: dict) -> list[str]:
        """Render the request body of an operation."""
        body = self.resolve(body)
        content = body.get('content', {})

        if not content:
            return []

        content_types = ', '.join(inline_code(c) for c in content)
        required = ' (required)' if body.get('required') else ''

        # Prefer the JSON representation for documentation purposes
        media = content.get('application/json') or next(iter(content.values()))
        schema = media.get('schema', {})

        lines = [
            f'**Request body**{required}: {self.type_str(schema)}',
            '',
            f'Content types: {content_types}',
            '',
        ]

        lines += self.example_block(schema, 'request', 'Example request body')

        return lines

    def render_responses(self, responses: dict) -> list[str]:
        """Render the responses of an operation."""
        if not responses:
            return []

        lines = [
            '**Responses**',
            '',
            '| Status | Description | Schema |',
            '| --- | --- | --- |',
        ]

        examples = []

        for status, response in responses.items():
            response = self.resolve(response)
            content = response.get('content', {})
            media = content.get('application/json') or (
                next(iter(content.values())) if content else {}
            )
            schema = media.get('schema', {}) if media else {}

            lines.append(
                f'| {inline_code(status)} '
                f'| {escape_cell(response.get("description", ""))} '
                f'| {self.type_str(schema) if schema else ""} |'
            )

            # Provide an example for successful JSON responses only
            if schema and str(status).startswith('2') and not examples:
                examples = self.example_block(
                    schema, 'response', f'Example response ({status})'
                )

        return [*lines, '', *examples]

    def render_operation(
        self, path: str, method: str, operation: dict, default_security: tuple
    ) -> list[str]:
        """Render a single API operation (path + method)."""
        anchor = operation_anchor(method, path)
        label = method.upper()

        lines = [
            f'### <span class="api-method api-method-{method}">{label}</span> '
            f'{inline_code(path)} {{#{anchor}}}',
            '',
        ]

        if operation.get('deprecated'):
            lines += [
                '!!! warning "Deprecated"',
                '    This endpoint is deprecated.',
                '',
            ]

        if summary := operation.get('summary'):
            lines += [f'**{escape_text(summary).strip()}**', '']

        if description := operation.get('description'):
            lines += [escape_text(description).strip(), '']

        security = self.security_names(operation.get('security'))

        if security != default_security:
            lines += [f'**Authentication**: {self.render_security(security)}', '']

        lines += self.render_parameters(operation.get('parameters', []))
        lines += self.render_request_body(operation.get('requestBody', {}))
        lines += self.render_responses(operation.get('responses', {}))

        return lines

    # ------------------------------------------------------------------ #
    # Component schemas
    # ------------------------------------------------------------------ #

    def render_schema(self, name: str) -> list[str]:
        """Render a single named component schema."""
        schema = self.schemas.get(name, {})

        lines = [f'### {name} {{#{schema_anchor(name)}}}', '']

        if description := schema.get('description'):
            lines += [escape_text(description).strip(), '']

        properties = schema.get('properties', {})

        if properties:
            required = set(schema.get('required', []))

            lines += [
                '| Field | Type | Required | Description |',
                '| --- | --- | --- | --- |',
            ]

            for field, prop in properties.items():
                flags = self.merged(prop)
                resolved = self.merged(self.resolve(prop))

                notes = []
                badges = []

                if flags.get('readOnly'):
                    badges.append('read-only')
                if flags.get('writeOnly'):
                    badges.append('write-only')
                if flags.get('nullable'):
                    badges.append('nullable')

                if badges:
                    notes.append(' '.join(f'*{b}*' for b in badges))

                if title := flags.get('title'):
                    if title.lower() != field.replace('_', ' ').lower():
                        notes.append(f'**{escape_cell(title)}**')

                field_description = flags.get('description') or resolved.get(
                    'description'
                )
                notes.append(escape_cell(field_description))

                # Constraints of referenced schemas are documented on that schema
                notes += self.constraints(flags, field_description)

                lines.append(
                    f'| {inline_code(field)} '
                    f'| {self.type_str(prop)} '
                    f'| {"Yes" if field in required else "No"} '
                    f'| {"<br>".join(n for n in notes if n)} |'
                )

            lines.append('')

        elif 'enum' in schema:
            base_type = self.type_str({k: v for k, v in schema.items() if k != 'enum'})
            lines += [f'Type: {base_type}', '']

            # Only list the values if the description does not already do so
            if self.constraints({'enum': schema['enum']}, description or ''):
                lines += ['| Value |', '| --- |']
                lines += [f'| {inline_code(json.dumps(v))} |' for v in schema['enum']]
                lines.append('')

        else:
            lines += [f'Type: {self.type_str(schema)}', '']

            if notes := self.constraints(schema):
                lines += ['<br>'.join(notes), '']

        return lines

    # ------------------------------------------------------------------ #
    # Page rendering
    # ------------------------------------------------------------------ #

    def default_security(self, paths: dict) -> tuple:
        """Return the most common set of security schemes across the given paths."""
        counts = {}

        for methods in paths.values():
            for method, operation in methods.items():
                if method in HTTP_METHODS:
                    key = self.security_names(operation.get('security'))
                    counts[key] = counts.get(key, 0) + 1

        if not counts:
            return ()

        return max(counts, key=counts.get)

    def render_page(self, title: str, paths: dict) -> str:
        """Render a full documentation page for a subset of API paths.

        Arguments:
            title: The title of this section of the API
            paths: Dict of {path: {method: operation}} items to render
        """
        info = self.spec.get('info', {})
        default_security = self.default_security(paths)

        lines = [
            '---',
            f'title: {json.dumps(title)}',
            # Schema text must never be interpreted as Jinja2 template code
            'render_macros: false',
            '---',
            '',
            f'The *{escape_text(title)}* section of the InvenTree API schema is documented below.',
            '',
            f'!!! info "API Version {escape_text(info.get("version", ""))}"',
            '    This page was generated automatically from the InvenTree API schema.',
            '',
        ]

        if default_security:
            lines += [
                '## Authentication',
                '',
                'Unless otherwise noted, endpoints on this page accept the following authentication methods: '
                + self.render_security(default_security)
                + '. Refer to the [API documentation](../index.md#authentication) for more information.',
                '',
            ]

        lines += ['## Endpoints', '']

        referenced = set()

        for path in sorted(paths):
            methods = paths[path]

            # Parameters may also be declared at the path level (shared by all methods)
            path_params = methods.get('parameters', [])

            for method in HTTP_METHODS:
                if operation := methods.get(method):
                    if path_params:
                        operation = {
                            **operation,
                            'parameters': path_params + operation.get('parameters', []),
                        }

                    lines += self.render_operation(
                        path, method, operation, default_security
                    )
                    self.collect_schema_refs(operation, referenced)

        if referenced:
            lines += ['## Schemas', '']

            for name in sorted(referenced, key=str.lower):
                lines += self.render_schema(name)

        return '\n'.join(lines).rstrip() + '\n'
