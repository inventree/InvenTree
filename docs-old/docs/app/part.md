---
title: Part Views
---

## Part Category View

From the *home screen*, select *Parts* to open the top-level part category view.

### Details Tab

The *Details* tab shows information about the selected part category. In particular, it shows the name and description of the category, a link to the parent category (if available) and a list of subcategories.

{% with id="part-category", url="part_category_detail.png" %}
{% include "app_img.html" %}
{% endwith %}

#### Parent Category

If the current category has a parent category (i.e. it is not a top-level category) then a link is provided to the parent category. Tap the *parent category* tile to navigate to the category detail page for the parent category.

#### Subcategories

If the current category has any subcategories, these are listed here. Select any of the subcategories to navigate to it.

### Parts Tab

The *Parts* tab displays all the parts available in this category. Tap a displayed part to navigate to the part detail view.

{% with id="cat-parts", url="category_parts_tab.png" %}
{% include "app_img.html" %}
{% endwith %}

The list of available parts can be filtered using the input box at the top of the screen:

{% with id="cat-parts-filter", url="category_parts_filter.png" %}
{% include "app_img.html" %}
{% endwith %}

### Context Actions

The following *Context Actions* are available for the selected category:

{% with id="cat-actions", url="category_actions_tab.png" %}
{% include "app_img.html" %}
{% endwith %}

#### New Category

Create a new subcategory under the current category:

{% with id="cat-new-cat", url="new_category.jpg" %}
{% include "app_img.html" %}
{% endwith %}

#### New Part

Create a new part within the current category:

{% with id="cat-new-part", url="new_part.jpg" %}
{% include "app_img.html" %}
{% endwith %}

### Edit Category

Select the *Edit* button in the top right corner of the screen to edit the details for the selected part category:

{% with id="cat-edit", url="part_category_edit.jpg" %}
{% include "app_img.html" %}
{% endwith %}

!!! info "Permission Required"
    If the user does not have permission to edit part details, this button will be hidden

In the part category display screen, there are three tabs of information available:

## Part Detail View

The *Part Detail* view displays information about a single part:

{% with id="part-details", url="part_details.png" %}
{% include "app_img.html" %}
{% endwith %}

### Details Tab

The *details* tab shows information about the selected part. Some of the displayed tiles provide further information when selected:

#### Category

Tap on the displayed part category to navigate to a detail view for that category.

#### Stock

The *stock* tile shows the total quantity of stock available for the part. Tap on this tile to navigate to the *Stock Tab* view for this part.

#### Notes

Tap on the *notes* tile to view (and edit) the notes for this part:

{% with id="part-notes", url="part_notes.jpg" %}
{% include "app_img.html" %}
{% endwith %}

#### Attachments

Tap on the *attachments* tile to view the file attachments for this part:

{% with id="part-attachments", url="part_attachments.jpg" %}
{% include "app_img.html" %}
{% endwith %}

New attachments can be uploaded by tapping on the icons in the top right of the screen.

Select a particular attachment file to downloaded it to the local device.

### Stock Tab

The *Stock* tab displays all the stock items available for this part. Tap on a particular stock item to navigate to a detail view for that item.

{% with id="part-stock", url="part_stock.png" %}
{% include "app_img.html" %}
{% endwith %}

The list of available stock items can be filtered using the input box at the top of the screen.

### Actions Tab

The *Actions* tab displays the available actions for the selected part:

#### New Stock Item

Create a new stock item for this part:

{% with id="part-stock-new", url="new_stock_item.jpg" %}
{% include "app_img.html" %}
{% endwith %}

### Edit Part

To edit the part details, select the *Edit* button in the top right corner of the screen:

{% with id="part-edit", url="part_edit.jpg" %}
{% include "app_img.html" %}
{% endwith %}

!!! info "Permission Required"
    If the user does not have permission to edit part details, this button will be hidden

### Part Image View

Tap the image of the part (displayed at the top left of the screen) to launch the part image view:

{% with id="part-image", url="part_image.jpg" %}
{% include "app_img.html" %}
{% endwith %}

A full-screen view of the image is displayed. The user can also upload a new image for the part, either selecting an image from the device, or taking a new picture with the device's camera.
