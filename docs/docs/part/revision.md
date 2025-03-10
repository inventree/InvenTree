---
title: Part Revisions
---

## Part Revisions

When creating a complex part (such as an assembly comprised of other parts), it is often necessary to track changes to the part over time. For example, throughout the lifetime of an assembly, it may be necessary to adjust the bill of materials, or update the design of the part.

Rather than overwrite the existing part data, InvenTree allows you to create a new *revision* of the part. This allows you to track changes to the part over time, and maintain a history of the part design.

Crucially, creating a new *revision* ensures that any related data entries which refer to the original part (such as stock items, build orders, purchase orders, etc) are not affected by the change.

### Revisions are Parts

A *revision* of a part is itself a part. This means that each revision of a part has its own part number, stock items, parameters, bill of materials, etc. The only thing that differentiates a *revision* from any other part is that the *revision* is linked to the original part.

### Revision Fields

Each part has two fields which are used to track the revision of the part:

* **Revision**: The revision number of the part. This is a user-defined field, and can be any string value.
* **Revision Of**: A reference to the part of which *this* part is a revision. This field is used to keep track of the available revisions for any particular part.

### Revision Restrictions

When creating a new revision of a part, there are some restrictions which must be adhered to:

* **Circular References**: A part cannot be a revision of itself. This would create a circular reference which is not allowed.
* **Unique Revisions**: A part cannot have two revisions with the same revision number. Each revision (of a given part) must have a unique revision code.
* **Revisions of Revisions**: A single part can have multiple revisions, but a revision cannot have its own revision. This restriction is in place to prevent overly complex part relationships.
* **Template Revisions**: A part which is a [template part](./template.md) cannot have revisions. This is because the template part is used to create variants, and allowing revisions of templates would create disallowed relationship states in the database. However, variant parts are allowed to have revisions.
* **Template References**: A part which is a revision of a variant part must point to the same template as the original part. This is to ensure that the revision is correctly linked to the original part.

## Revision Settings

The following options are available to control the behavior of part revisions.

Note that these options can be changed in the InvenTree settings:

{% with id="part_revision_settings", url="part/part_revision_settings.png", description="Part revision settings" %}
{% include 'img.html' %}
{% endwith %}

* **Enable Revisions**: If this setting is enabled, parts can have revisions. If this setting is disabled, parts cannot have revisions.
* **Assembly Revisions Only**: If this setting is enabled, only assembly parts can have revisions. This is useful if you only want to track revisions of assemblies, and not individual parts.

## Create a Revision

To create a new revision for a given part, navigate to the part detail page, and click on the "Revisions" tab.

Select the "Duplicate Part" action, to create a new copy of the selected part. This will open the "Duplicate Part" form:

{% with id="part_create_revision", url="part/part_create_revision.png", description="Create part revision" %}
{% include 'img.html' %}
{% endwith %}

In this form, make the following updates:

1. Set the *Revision Of* field to the original part (the one that you are duplicating)
2. Set the *Revision* field to a unique revision number for the new part revision

Once these changes (and any other required changes) are made, press *Submit* to create the new part.

Once the form is submitted (without any errors), you will be redirected to the new part revision. Here you can see that it is linked to the original part:

{% with id="part_revision_b", url="part/part_revision_b.png", description="Revision B" %}
{% include 'img.html' %}
{% endwith %}

## Revision Navigation

When multiple revisions exist for a particular part, you can navigate between revisions using the *Select Part Revision* drop-down which renders at the top of the part page:

{% with id="part_revision_select", url="part/part_revision_select.png", description="Select part revision" %}
{% include 'img.html' %}
{% endwith %}

Note that this revision selector is only visible when multiple revisions exist for the part.
