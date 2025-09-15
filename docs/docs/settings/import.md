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

### Required Permissions

To import data, the user must have the appropriate permissions. The user must be a *staff* user, and have the `change` permission for the model in question.

## Import Session

Importing data is a multi-step process, which is managed via an *import session*. An import session is created when the user initiates a data import, and is used to track the progress of the data import process.

### Import Session List

The import session is managed by the InvenTree server, and all import session data is stored on the server. As the import process can be time-consuming, the user can navigate away from the import page and return later to check on the progress of the import.

Import sessions can be managed from the [Admin Center](./admin.md#admin-center) page, which lists all available import sessions

### Context Sensitive Importing

Depending on the type of data being imported, an import session can be created from an appropriate page context in the user interface. In such cases, the import session will be automatically linked to the relevant data type being imported.

## Import Process

The following steps outline the process of importing data into InvenTree:

### Create Import Session

An import session can be created via the methods outlined above. The first step is to create an import session, and upload the data file to import. Note that depending on the context of the data import, the user may have to select the database model to import data into.

{{ image("admin/import_session_create.png", "Create import session") }}

### Map Data Fields

Next, the user must map the data fields in the uploaded file to the fields in the database model. This is a critical step, as the data fields must be correctly matched to the database fields.

{{ image("admin/import_session_map.png", "Map data fields") }}

The InvenTree server will attempt to automatically associate the data fields in the uploaded file with the database fields. However, the user may need to manually adjust the field mappings to ensure that the data is imported correctly.

### Import Data

Once the data fields have been mapped, the data is loaded from the file, and stored (temporarily) in the import session. This step is performed automatically by the InvenTree server once the user has confirmed the field mappings.

Note that this process may take some time if the data file is large. The import process is handled by the background worker process, and the user can navigate away from the import page and return later to check on the progress of the import.

### Process Data

Once the data has been loaded into the import session, the user can process the data. This step will attempt to validate the data, and check for any errors or issues that may prevent the data from being imported.

{{ image("admin/import_session_process.png", "Process data") }}

Note that each row must be selected and confirmed by the user before it is actually imported into the database. Any errors which are detected will be displayed to the user, and the user can choose to correct the data and re-process it.

During the processing step, the status of each row is displayed at the left of the table. Each row can be in one of the following states:

- **Error**: The row contains an error which must be corrected before it can be imported.
- **Pending**: The row contains no errors, and is ready to be imported.
- **Imported**: The row has been successfully imported into the database.

Each individual row can be imported, or removed (deleted) by the user. Once all the rows have been processed, the import session is considered *complete*.

### Import Completed

Once all records have been processed, the import session is considered complete. The import session can be closed, and the imported records are now stored in the database.

## Updating Existing Records

The data import process can also be used to update existing records in the database. This requires that the imported data file contains a unique identifier for each record, which can be used to match the records in the database.

The basic outline of this process is:

1. Export the existing records to a CSV file.
2. Modify the CSV file to update the records as required.
3. Upload the modified CSV file to the import session.

!!! note "Mixing Creation and Update"
    It is not possible to mix the creation of new records with the updating of existing records in a single import session. If you wish to create new records, you must create a separate import session for that purpose.

### Create Import Session

!!! note "Admin Center"
    Updating existing records can only be performed when creating a new import session from the [Admin Center](./admin.md#admin-center).

Create a new import session, and ensure that the *Update Existing Records* option is selected. This will allow the import session to update existing records in the database.

{{ image("admin/import_session_create_update.png", "Update existing records") }}

### Map Data Fields

When mapping the data fields, ensure that the `ID` field is correctly mapped to the corresponding column in the file:

{{ image("admin/import_select_id.png", "Update existing records") }}

### Process Data

When processing the data, each row will be matched against an existing record in the database. If a match is found, the existing record will be updated with the new data from the imported file.

{{ image("admin/import_update_process.png", "Update existing records") }}
