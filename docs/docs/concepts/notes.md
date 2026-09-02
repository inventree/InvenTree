---
title: Notes
---

## Notes

*Notes* allow free-form rich-text content to be written and stored against a specific object within InvenTree. Notes can be used to record observations, instructions, historical context, or any other information associated with a model instance.

!!! note "Business Logic"
    Notes are not to be used for any core business logic within InvenTree. They are intended to provide supplementary documentation and context for objects, which can be useful for reference, communication, or reporting purposes. Plugins should not use them for storage and opt for object metadata or custom models instead.

Notes can be associated with various InvenTree models, and each model can have multiple notes associated with it. The user interface provides a dedicated "Notes" tab on the detail page of any model that supports notes, allowing users to easily view and manage notes for that object.

### Notes Tab

Any model which supports notes will have a "Notes" tab on its detail page. This tab displays the content of the currently selected note, along with a sidebar listing all notes for that object by title:

{{ image("concepts/notes-tab.png", "Notes Tab Example") }}

## Note Fields

Each note has the following attributes:

| Field | Description |
| --- | --- |
| Title | A short title for the note (*required*) |
| Description | An optional brief description of the note's purpose |
| Content | The rich-text body of the note |
| Primary | Marks this note as the default note for the object |

## Primary Note

When a model has multiple notes, one may be designated as the *primary* note. The primary note is indicated by a {{ icon("star") }} icon in the note sidebar.

- When the first note is created for a model instance, it is automatically set as the primary note.
- Only one note per model instance can be marked as primary at any time.
- The primary note is opened by default when navigating to the Notes tab.

## Rich Text Editing

Note content is edited using a rich-text (WYSIWYG) editor. The following formatting options are available:

- **Text formatting**: Bold, italic, underline, strikethrough, inline code, code blocks
- **Headings**: H1 through H4
- **Structure**: Blockquotes, horizontal rules
- **Lists**: Bullet lists and ordered lists
- **Links**: Insert and remove hyperlinks
- **Tables**: Insert tables; add/remove rows and columns; toggle header rows
- **Images**: Embed images uploaded directly into the note

### Inserting Images

Images can be embedded in note content in the following ways:

- Click the {{ icon("photo") }} button in the editor toolbar to select a file from your device
- Paste an image directly from the clipboard
- Drag and drop an image file into the editor

Uploaded images are stored on the server and linked to the note. If a note is edited or deleted, any images that are no longer referenced by any note are automatically removed.

## Adding a Note

To add a note to an object:

1. Navigate to the object's detail page
2. Click on the **Notes** tab
3. Click the **Add Note** button
4. Fill in the `Title` (required) and optional `Description` fields
5. Click **Submit**

The new note will appear in the sidebar ready for editing.

## Editing Note Content

Note content is shown in read-only mode by default. To make changes:

1. Click the {{ icon("pencil") }} icon in the note header to enter edit mode
2. Use the toolbar to format content, insert images, or add tables
3. Click the {{ icon("device-floppy") }} icon, or press **Ctrl+S** / **Cmd+S**, to save changes
4. Click the {{ icon("check") }} icon to exit edit mode once all changes are saved

!!! warning "Unsaved Changes"
    If you navigate away from the Notes panel or leave the page while in edit mode with unsaved changes, InvenTree will prompt you to confirm before proceeding.

### Resetting Changes

While in edit mode, clicking the {{ icon("reload") }} icon discards any unsaved changes and reloads the last saved version of the note.

## Editing Note Properties

To change a note's title or description, open the actions menu in the note header and select **Edit Note**.

## Deleting a Note

To delete a note, open the actions menu in the note header and select **Delete Note**.

!!! danger "Permanent Action"
    Deleting a note is permanent and cannot be undone. Any images embedded in the note that are not referenced elsewhere will also be removed.

## Note Templates

Note templates are pre-defined notes that can be used as a starting point when adding a new note to any model instance. They allow administrators to standardize common note structures and reduce repetitive data entry.

### Creating Notes from Templates

When adding a new note to an object, an optional **From Template** field is available. Selecting a template pre-fills the **Title**, **Description**, and **Content** fields with the template's content. These fields can then be edited before saving.

To create a note from a template:

1. Navigate to the object's detail page and open the **Notes** tab
2. Click the **Add Note** button
3. In the **From Template** field, select an existing template from the dropdown
4. The **Title**, **Description**, and **Content** fields are automatically populated from the template
5. Edit any fields as needed
6. Click **Submit** to save the note

!!! info "Template Filters"
    The template dropdown only shows templates that are applicable to the current model type, plus any templates that are not restricted to a specific model type.

### Managing Note Templates

Note templates are managed by staff users via the **Admin Center**.

To access note templates:

1. Navigate to **Settings** > **Admin Center**
2. Select the **Note Templates** panel

This panel provides the same rich-text editor interface used for regular notes. Templates created here are available to all users when adding notes across the system.

#### Creating a Template

1. In the **Note Templates** panel, click **Add Note Template**
2. Enter a **Title** (required) and optional **Description**
3. Optionally select a **Model Type** to restrict the template to a specific kind of object (e.g. *Part*, *Build Order*). Leave blank to make the template available for all model types
4. Click **Submit**, then edit the template content in the editor

#### Editing a Template

Select a template from the sidebar, then use the same edit workflow as for regular notes: click the {{ icon("pencil") }} icon, make changes, and save with {{ icon("device-floppy") }} or **Ctrl+S** / **Cmd+S**.

#### Deleting a Template

Open the actions menu in the template header and select **Delete Note Template**.

!!! note
    Deleting a template does not affect any notes that were previously created from it.
