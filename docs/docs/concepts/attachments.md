---
title: Attachments
---

## Attachments

An *attachment* is a file which has been uploaded and linked to a specific object within InvenTree. Attachments can be used to store additional documentation, images, or other relevant files associated with various InvenTree models.

!!! note "Business Logic"
    Attachments are not used for any core business logic within InvenTree. They are intended to provide additional metadata for objects, which can be useful for documentation, reference, or reporting purposes.

Parameters can be associated with various InvenTree models.

### Attachments Tab

Any model which supports attachments will have an "Attachments" tab on its detail page. This tab displays all attachments associated with that object:

{{ image("concepts/attachments-tab.png", "Order Attachments Example") }}

## Attachments Types

The following types of attachments are supported:

### File Attachments

File attachments allow users to upload files directly to InvenTree. These files are stored on the server and can be downloaded or viewed by users with appropriate permissions.

### Link Attachments

Link attachments allow users to associate external URLs with an object. This can be useful for linking to external documentation, resources, or other relevant web content.

## Adding Attachments

To add an attachment to an object, navigate to the object's detail page and click on the "Attachments" tab. From there, you can click the "Add attachment" button to upload a file or the "Add external link" button to add a link.

### Renaming Attachments

Once a file attachment has been uploaded, it can be renamed by clicking the "Edit" action associated with the attachment. This allows you to change the filename without needing to re-upload the file. The system will handle renaming the file on the server and updating the database record accordingly.
