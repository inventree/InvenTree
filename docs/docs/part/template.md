---
title: Part Templates
---

## Part Templates

There are various purposes for using Part Templates, among them:

* Template parts can hold information that can be re-used across "Variants", a template part could be useful for creating a base variant of an assembly which can be derived from, with BoM changes for instance.
* Variants can be used as "manufacturing variants" where the variant dictates a particular configuration which a customer can order: a variant might determine the particular options that come with a part, like harnesses, enclosure, color, specs, etc.

"Variants" parts will reference the "Template" part therefore explicitly creating and showing direct relationship.
They also allow you to do special things like:

* **Serial Numbers**
Parts that are linked in a template / variant relationship must have unique serial numbers (e.g. if you have a template part Widget, and two variants Widget-01 and Widget-02 then any assigned serial numbers must be unique across all these variants).
* **Stock Reporting**
The "stock" for a template part includes stock for all variants under that part.
* **Logical Grouping**
The template / variant relationship is subtly different to the category / part relationship.

### Enable Template Part

Any part can be set as "Template" part. To do so:

1. navigate to a specific part detail page
0. click on the "Details" tab
0. locate the part options on the right-hand side
0. toggle the `Template` option so it shows green / slider to the right:
{% with id="enable_template_part", url="part/enable_template_part.png", description="Enable Template Part Option" %}
{% include 'img.html' %}
{% endwith %}

### Create Variant

When a part's [*Template option*](#enable-template-part) is turned-on, "Variants" of this part can be created.

To create a variant, navigate to a specific part detail page, click on the "Variants" tab then click on the "New Variant" button.
The `Duplicate Part` form will be displayed. Fill it out then click on <span class="badge inventree confirm">Submit</span> to create the variant.
