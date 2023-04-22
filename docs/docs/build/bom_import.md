---
title: BOM Import
---

## Importing BOM Data

Uploading a BOM to InvenTree is a three steps process:

1. Upload BOM file
0. Select matching InvenTree fields
0. Select matching InvenTree parts.

To upload a BOM file, navigate to the part/assembly detail page then click on the "BOM" tab. On top of the tab view, click on the <span class='fas fa-edit'></span> icon then, after the page reloads, click on the <span class='fas fa-file-upload'></span> icon.

The following view will load:
{% with id="bom_upload_file", url="build/bom_upload_file.png", description="BOM Upload View" %}
{% include 'img.html' %}
{% endwith %}

#### Upload BOM File

Click on the "Choose File" button, select your BOM file when prompted then click on the "Upload File" button.

!!! info "BOM Formats"
	The following BOM file formats are supported: CSV, TSV, XLS, XLSX, JSON and YAML

#### Select Fields

Once the BOM file is uploaded, the following view will load:
{% with id="bom_select_fields", url="build/bom_select_fields.png", description="Select Fields View" %}
{% include 'img.html' %}
{% endwith %}

InvenTree will attempt to automatically match the BOM file columns with InvenTree part fields. `Part_Name` is a **required** field for the upload process and moving on to the next step. Specifying the `Part_IPN` field matching is very powerful as it allows to create direct pointers to InvenTree parts.

Once you have selected the corresponding InvenTree fields, click on the "Submit Selections" button to move on to the next step.

#### Select Parts

Once the BOM file columns and InvenTree fields are correctly matched, the following view will load:
{% with id="bom_select_parts", url="build/bom_select_parts.png", description="Select Parts View" %}
{% include 'img.html' %}
{% endwith %}

InvenTree automatically tries to match parts from the BOM file with parts in its database. For parts that are found in InvenTree's database, the `Select Part` field selection will automatically point to the matching database part.

In this view, you can also edit the parts `Reference` and `Quantity` fields.

Once you have selected the corresponding InvenTree parts, click on the "Submit BOM" button to complete the BOM upload process.
