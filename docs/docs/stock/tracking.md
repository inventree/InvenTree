---
title: Stock Tracking
---

## Stock Tracking

It may be desirable to track individual stock items, or groups of stock items, with unique identifier values. Stock items may be *tracked* using either *Batch Codes* or *Serial Numbers*.

Individual stock items can be assigned a batch code, or a serial number, or both, or neither, as requirements dictate.

{% with id="batch_and_serial", url="stock/batch_and_serial.png", description="Batch and serial number" %}
{% include 'img.html' %}
{% endwith %}

Out of the box, the default implementations for both batch codes and serial numbers are (intentionally) simplistic.

As the particular requirements for serial number or batch code conventions may vary significantly from one application to another, InvenTree provides the ability for custom plugins to determine exactly how batch codes and serial numbers are implemented.

### Batch Codes

Batch codes can be used to specify a particular "group" of items, and can be assigned to any stock item without restriction. Batch codes are tracked even as stock items are split into separate items.

Multiple stock items may share the same batch code without restriction, even across different parts.

#### Generating Batch Codes

Batch codes can be generated automatically based on a provided pattern. The default pattern simply uses the current datecode as the batch number, however this can be customized within a certain scope.

{% with id="batch_code_pattern", url="stock/batch_code_template.png", description="Batch code pattern" %}
{% include 'img.html' %}
{% endwith %}

#### Context Variables

The following context variables are available by default when generating a batch code using the builtin generation functionality:

| Variable | Description |
| --- | --- |
| year | The current year e.g. `2024` |
| month | The current month number, e.g. `5` |
| day | The current day of month, e.g. `21` |
| hour | The current hour of day, in 24-hour format, e.g. `23` |
| minute | The current minute of hour, e.g. `17` |
| week | The current week of year, e.g. `51` |

#### Plugin Support

To implement custom batch code functionality, refer to the details on the [Validation Plugin Mixin](../extend/plugins/validation.md#batch-codes).

### Serial Numbers

A serial "number" is used to uniquely identify a single, unique stock item. Note that while *number* is used throughout the documentation, these values are not required to be numeric.

#### Uniqueness Requirements

By default, serial numbers must be unique across any given [Part](../part/part.md) instance (including any variants of that part).

However, it is also possible to specify that serial numbers must be globally unique across all types of parts. This is configurable in the settings display (see below):

{% with id="serial_numbers_unique", url="stock/serial_numbers_unique.png", description="Serial number uniqueness" %}
{% include 'img.html' %}
{% endwith %}

#### Generating Serial Numbers

When creating a group of serialized stock items, it can be very useful for the user to be able to generate a group of unique serial numbers, with one serial number for each serialized stock item.

{% with id="serial_next", url="stock/serial_next.png", description="Serial number entry" %}
{% include 'img.html' %}
{% endwith %}

For a given serial number *schema* (either the in-built schema or a custom schema defined by a plugin), a group (or *range*) of serial numbers can be generated using a number of possible patterns:

##### Comma Separated Values

Individual serial numbers can be specified by separating using a comma character (`,`).

| Pattern | Serial Numbers |
| --- | --- |
| `1, 2, 45, 99, 101` | `1, 2, 45, 99, 101` |

##### Hyphen Separated Range

Use a hyphen character (`-`) to specify a *range* of sequential values, inclusive of the two values separated by the hyphen.

| Pattern | Serial Numbers |
| --- | --- |
| `10-15` | `10, 11, 12, 13, 14, 15` |

##### Starting Value Range

A *starting value* can be supplied, followed by the plus (`+`) character to indicate a number of sequential values following the provided starting value. The `+` character should be followed by an integer value to indicate the number of serial numbers which will be generated.

| Pattern | Serial Numbers |
| --- | --- |
| `10+3` | `10, 11, 12, 13` |
| `100 + 2` | `100, 101, 102` |

##### Next Value

When specifying serial numbers, the tilde (`~`) character is replaced with the next available serial number. It can be used in combination with the available patterns specified above.

For example, if the *next* available serial number is `100`, the following patterns can be used:

| Pattern | Serial Numbers |
| --- | --- |
| `~` | `100` |
| `~, ~, ~` | `100, 101, 102` |
| `800, ~, 900` | `800, 100, 900` |
| `~+5` | `100, 101, 102, 103, 104, 105` |

##### Combination Groups

Any of the above patterns can be combined using multiple groups separated by the comma (`,`) character:

| Pattern | Serial Numbers |
| --- | --- |
| `1, 2, 4-7, 10` | `1, 2, 4, 5, 6, 7, 10` |
| `40+4, 50+4` | `40, 41, 42, 43, 44, 50, 51, 52, 53, 54` |
| `10, 14, 20+3, 30-35` | `10, 14, 20, 21, 22, 23, 30, 31, 32, 33, 34, 35` |

In the default implementation, InvenTree assumes that serial "numbers" are integer values in a simple incrementing sequence e.g. `{1, 2, 3, 4, 5, 6}`. When generating the *next* value for a serial number, the algorithm looks for the *most recent* serial number, and attempts to coerce that value into an integer, and then increment that value.

While this approach is reasonably robust, it is definitely simplistic and is not expected to meet the requirements of every installation. For this reason, more complex serial number management is intended to be implemented using a custom plugin (see below).

#### Serial Number Errors

If a provided serial number (or group of numbers) is not considered valid, an error message is provided to the user.

##### Example: Invalid Quantity

{% with id="serial_error_quantity", url="stock/serial_error_quantity.png", description="Serial number - invalid quantity" %}
{% include 'img.html' %}
{% endwith %}

##### Example: Duplicate Serial Numbers

{% with id="serial_error_unique", url="stock/serial_error_unique.png", description="Serial number - duplicate values" %}
{% include 'img.html' %}
{% endwith %}

##### Example: Invalid Serial Numbers

!!! tip "Serial Number Validation"
    Custom serial number validation can be implemented using an external plugin

#### Plugin Support

Custom serial number functionality, with any arbitrary requirements or level of complexity, can be implemented using the [Validation Plugin Mixin class](../extend/plugins/validation.md#serial-numbers). Refer to the documentation for this plugin for technical details.

A custom plugin allows the user to determine how a "valid" serial number is defined, and (crucially) how any given serial number value is incremented to provide the next value in the sequence.

Implementing custom methods for these two consideraions allows for complex serial number schema to be supported with minimal effort.
