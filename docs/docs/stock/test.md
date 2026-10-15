---
title: Stock Test Result
---

## Stock Test Result

Stock items which are associated with a [testable part](../part/index.md#testable) can have associated test data - this is particularly useful for tracking unit testing / commissioning / acceptance data against a serialized stock item.

The tests which can be recorded against a stock item are determined by the [part tests](../part/test.md#part-tests) which apply to the stock item's part - including tests which are [inherited](../part/test.md#test-inheritance) from template parts and part categories.

{{ image("stock/test_results.png", title="Stock Item Test Results") }}

### Test Result Fields

| Field | Description |
| --- | --- |
| Test Template | The [test template](../part/test.md#test-templates) against which the result is recorded. Each test result must link to a test template. |
| Result | Boolean pass/fail status of the test |
| Value | Optional value recorded as part of the test. For example if the test is to record the firmware version of a programmed device, the version number can be added here. If the template [requires a value](../part/test.md#test-template-fields), this field must be provided. If the template defines *choices*, the value must match one of the available choices. |
| Attachment | Optional file attachment containing extra test information. If the template [requires an attachment](../part/test.md#test-template-fields), an attachment must be provided. |
| Notes | Optional field available for extra notes |
| Test Station | The test station on which the test was performed *(only available if [test station data](#test-station-data) is enabled)* |
| Started | The date and time at which the test was started *(only available if [test station data](#test-station-data) is enabled)* |
| Finished | The date and time at which the test was finished *(only available if [test station data](#test-station-data) is enabled)* |
| User | The user who recorded the test result (set automatically) |
| Date | The date at which the test result was recorded (set automatically) |

### Test Template Validation

A new test result can only be recorded against a test template which *applies* to the stock item's part - i.e. a test template which is linked to the part (or a template part, or the part's category) via a [part test](../part/test.md#part-tests). Attempting to record a result against any other test template will fail with a validation error.

This check applies to *disabled* tests as well: results can still be recorded against a test which has been disabled for the part.

!!! info "Adding a New Test"
    To record results for a test which does not yet apply to a part, first [link the test template](../part/test.md#linking-tests-to-a-part) to the part (or its category).

### Multiple Test Results

Multiple results can be uploaded against the same test. In cases where multiple test results are uploaded, the most recent value is used to determine the pass/fail status of the test. It is useful to keep all test records as a given test might be required to run multiple times, if (for example) it fails the first time and then something must be fixed before running the test again.

### Required Tests

A stock item is considered to have *passed all required tests* if, for every test which is [required and enabled](../part/test.md#part-test-fields) for the stock item's part, the most recent test result is a *pass*.

The pass status of required tests is used in a number of places:

- **Build Orders:** Build outputs can be prevented from being completed until all required tests have passed. Refer to the [build order settings](../manufacturing/build.md#build-order-settings).
- **Sales Orders:** Stock items can be prevented from being allocated to a sales order until all required tests have passed. Refer to the [sales order settings](../sales/sales_order.md#sales-order-settings).

### Installed Items

When displaying test results for a stock item, test results recorded against any stock items which are *installed* in that stock item are also displayed. If the same test has a result recorded against both the parent stock item and an installed item, the result recorded against the parent stock item takes precedence.

### Test Station Data

If the {{ globalsetting("TEST_STATION_DATA", short=True) }} setting is enabled, additional information about the test station, and the test start and finish times, can be recorded against each test result.

### Deleting Test Templates

!!! danger "Deleting Test Templates"
    Deleting a [test template](../part/test.md#test-templates) will also delete *all* test results recorded against that template. Test templates are shared across parts, so this may delete results for many different parts.

### Reporting

The following test result data is available in the [report context](../report/context_variables.md) for stock items:

| Variable | Description |
| --- | --- |
| `results` | Dict of the most recent test results, keyed by [test key](../part/test.md#test-key) (including results from installed items) |
| `result_list` | List of the most recent test results (including results from installed items) |
| `tests` | Dict of the most recent test results, keyed by test key (excluding installed items) |
| `test_keys` | List of the test keys associated with the stock item (including tests which have no result yet) |
| `test_templates` | Dict of the [test templates](../part/test.md#reporting) which apply to the stock item's part, keyed by test key |
| `test_template_list` | List of the test templates which apply to the stock item's part |

For any information regarding the reporting architecture, please refer to the [Report Generation](../report/report.md) page. A sample [test report](../report/samples.md#test-report) template is provided with InvenTree.

### Automated Test Integration

The stock item testing framework is especially useful when integrating with an automated acceptance testing framework. Test results can be uploaded using the [InvenTree API](../api/index.md) or the [InvenTree Python Interface](../api/python/index.md).

When uploading test results via the API, the test template can be specified either by the template ID (`template` field), or by the test name (`test` field). If the test name is provided, InvenTree will look up the matching [test key](../part/test.md#test-key) from the tests which apply to the stock item's part.

!!! info "Example"
	You design and sell a temperature sensor which needs to be calibrated before it can be sold. An automated calibration tool sets the offset in the device, and uploads a test result to the InvenTree database.
