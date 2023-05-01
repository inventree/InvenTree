---
title: Model Metadata
---

## Model Metadata

The API is *self describing* in that it provides metadata about the various fields available at any given endpoint. External applications (such as the [python interface](../api/python/python.md)) can introspect the API to determine information about the model fields.

!!! tip "API Forms"
    The various forms implemented in the InvenTree web interface make heavy use of this metadata feature

### Requesting Metadata

To request metadata about a particular API endpoint, simply perform an `OPTIONS` method request against the API URL.

For example, to view the metadata available for creating a new [Part Category](../part/part.md#part-category), an `OPTIONS` request to `/api/part/category/` yields:

{% with id="api_cat_options", url="api/api_category_options.png", description="Part category options" %}
{% include 'img.html' %}
{% endwith %}

You can see here a detailed list of the various fields which are available for this API endpoint.

## Metadata Information

The `OPTIONS` endpoint provides the following information:

| Entry | Description |
| --- | --- |
| name | The human-readable name of the API endpoint |
| description | Descriptive detail for the endpoint, extracted from the python docstring |
| actions | Contains the available HTTP actions and field information (see below) |

Specific details are provided on the available attributes of each field:

{% with id="api_fields", url="api/api_metadata_fields.png", description="Metadata fields" %}
{% include 'img.html' %}
{% endwith %}

### Field Types

Supported field types are:

| Field Type | Description |
| --- | --- |
| string | Text data |
| boolean | true / false value |
| integer | Integer numbers |
| float | Floating point numbers |
| related field | Primary key value for a foreign-key relationship in the database |

### Field Attributes

Each named field provides information on available attributes:

| Attribute | Description |
| --- | --- |
| type | Defines the [field type](#field-types) |
| default | The default value for this field. Will be assumed if no value is supplied |
| required | Boolean value, whether this field must be supplied |
| read_only | Boolean value, whether this field is writeable |
| label | Human readable descriptive label for this field. |
| help_text | Long form descriptor for this field. |
| min_value | Minimum allowed value (for numeric fields) |
| max_value | Maximum allowed value (for numeric fields) |
| max_length | Maximum allowed length (for text fields) |
| model | Name of the database model, if this field represents a foreign-key relationship |
| api_url | API url for the related model, if this field represents a foreign-key relationship |
| filters | API filters for the field, if this field represents a foreign-key relationship |

!!! tip "Field Name"
    The field name is the *key* used to define the field itself

!!! info "Available Attributes"
    Some attributes may not be made available for a particular field



## Translation

Field *label* and *help text* values are localized using the [community contributed translations](https://crowdin.com/project/inventree). The required locale information is determined from the API request itself, meaning that the translated values are provided automatically.

For example, the same forms (in the web interface) are served via identical API requests, with the locale information determined "on the fly":

{% with id="api_english", url="api/api_english.png", description="API forms (english)" %}
{% include 'img.html' %}
{% endwith %}

{% with id="api_german", url="api/api_german.png", description="API forms (german)" %}
{% include 'img.html' %}
{% endwith %}
