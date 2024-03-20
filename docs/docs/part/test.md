---
title: Part Test Templates
---

## Part Test Templates

Parts which are designated as *trackable* (meaning they can be uniquely serialized) can define templates for tests which are to be performed against individual stock items corresponding to the part.

A test template defines the parameters of the test; the individual stock items can then have associated test results which correspond to a test template.

Test templates "cascade" down to variant parts: this means that if a master part has multiple variants, any test template defined for the master part will be assigned to the variants. Any stock items of the variant parts will have the same test templates associated with them.

{% with id="part_test_templates", url="part/part_test_templates.png", description="Part Test Templates" %}
{% include 'img.html' %}
{% endwith %}

### Test Template Parameters

#### Test Name

The name of the test is a simple string value which defines the name of the test. This test must be unique for a given part (or across a set of part variants).

#### Test Key

The test name is used to generate a test "key" which is then used to match against test results associated with individual stock items. The *key* is a simplified string representation of the test name, which consists only of lowercase alphanumeric characters. This key value is automatically generated (based on the test name) whenever the test template is saved.

The generated test key is intended to be a valid python variable name, and can be used to reference the test in the report generation system.

##### Examples

Some examples of generated test key values are provided below:

| Test Name | Test Key |
| --- | --- |
| "Firmware Version" | "firmwareversion" |
| " My NEW T E sT " | "mynewtest" |
| "100 Percent Test"| "_100percenttest" *(note that the leading underscore is added to ensure the key is a valid python variable name)* |
| "Test 123" | "test123" |

#### Test Description

This field is a simple description for providing information back to the user. The description is not used by the InvenTree testing framework.

#### Required

If the *required* flag is set, this indicates that the test is crucial for the acceptance of a particular stock item.

#### Requires Value

If this flag is set, then a corresponding test result against a stock item must set the *value* parameter.

#### Requires Attachment

If this flag is set, then a corresponding test result against a stock item must provide a file attachment uploaded.

#### Enabled

Tests can be *disabled* by setting the *enabled* flag to `False`. This can be useful if a test is no longer required, but the test template should be retained for historical purposes. Note that *deleting* a test template will also delete any associated test results. So, if a test template is no longer required, it is better to disable it rather than delete it.

### Test Results

Individual stock item objects can have test results associated with them which correspond to test templates. Refer to the [stock test result](../stock/test.md) documentation for further information.
