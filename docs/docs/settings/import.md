---
title: Importing Data
---

## Importing Data

External data can be imported via the admin interface, allowing for rapid integration of existing datasets, or bulk editing of table data.

!!! danger "Danger"
    Uploading bulk data directly is a non-reversible action.

!!! warning "Backup"
    Ensure you have made a backup of your database before performing bulk data import.

!!! warning "Supported Models"
    Not all models in the InvenTree database support bulk import actions.

When viewing a model (which supports bulk data import) in the admin interface, select the "Import" button in the top-right corner:

{% with id="import", url="admin/import.png", description="Data import" %}
{% include 'img.html' %}
{% endwith %}

The next screen displays a list of column headings which are expected to be present in the uploaded data file.

{% with id="import_upload", url="admin/import_upload.png", description="Data upload" %}
{% include 'img.html' %}
{% endwith %}

Select the data file to import, and the data format. Press the "Submit" button to upload the file.

### File Format

The uploaded data file must meet a number of formatting requirements for successful data upload. A simple way of ensuring that the file format is correct is to first [export data](./export.md) for the model in question, and delete all data rows (not the header row) from the exported data file.

Then, the same file can be used as a template for uploading more data to the server.

### ID Field

The uploaded data file requires a special field called `id`. This `id` field uniquely identifies each entry in the database table(s) - it is also known as a *primary key*.

The `id` column **must** be present in an uploaded data file, as it is required to know how to process the incoming data.

Depending on the value of the `id` field in each row, InvenTree will attempt to either insert a new record into the database, or update an existing one.

#### Empty ID

If the `id` field in a given data row is empty (blank), then InvenTree interprets that particular row as a *new* entry which will be inserted into the database.

If you wish for a new database entry to be created for a particular data row, the `id` field **must** be left blank for that row.

#### Non-Empty ID

If the `id` field in a given data row is *not* empty, then InvenTree interprets that particular row as an *existing* row to override / update.

In this case, InvenTree will search the database for an entry with the matching `id`. If a matching entry is found, then the entry is updated with the provided data.

However, if an entry is *not* found with the matching `id`, InvenTree will return an error message, as it cannot find the matching database entry to update.

!!! warning "Check id Value"
    Exercise caution when uploading data with the `id` field specified!

### Import Preview

After the data file has been uploaded and validated, the user is presented with a *preview* screen, showing the records that will be inserted or updated in the database.

Here the user has a final chance to review the data upload.

Press the *Confirm Import* button to actually perform the import process and commit the data into the database.

{% with id="import_preview", url="admin/import_preview.png", description="Data upload preview" %}
{% include 'img.html' %}
{% endwith %}

Note that *new* records are automatically assigned an `id` value.

## Import Errors

Manually importing data in a relational database is a complex process. You may be presented with an error message which describes why the data could not be imported.

The error message should contain enough information to manually edit the data file to fix the problem.

Any error messages are displayed per row, and you can hover the mouse over the particular error message to view specific error details:

{% with id="import_error", url="admin/import_error.png", description="Data upload error" %}
{% include 'img.html' %}
{% endwith %}


!!! info "Report Issue"
    If the error message does not provide enough information, or the error seems like a bug caused by InvenTree itself, report an [issue on Github](https://github.com/inventree/inventree/issues).
