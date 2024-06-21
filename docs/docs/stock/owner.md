---
title: Stock Ownership
---

## Stock Ownership

InvenTree supports stock ownership, which allows to set groups and users as "owners" of stock locations and items. The owners would be the only users who can edit and manage those stock locations and items.

The stock ownership feature is disabled by default, and must be enabled via the settings menu:

{% with id="stock_owner", url="stock/enable_stock_owner.png", description="Enable stock ownership feature" %}
{% include 'img.html' %}
{% endwith %}

### Background
The stock item ownership function does not change or the influence the access rights that have been set
in admin panel. It just hides buttons for edit, add and delete actions. This means that the user who
should have access by ownership needs to have stock item write access set in the admin panel. By
this he also gets write access to all other items, except the item has a different owner.

Example

* Stock item 1111 has an owner called Daniel
* Stock item 2222 has an owner called Peter
* Stock item 3333 has no owner

Set  stock item access for Daniel and Peter to V,A,E,D in the admin panel. Now Daniel can edit
1111 but not 2222. Peter can edit 2222 but not 1111. Both can edit 3333.


!!! warning "Existing Stock Locations and Items"
	Items with no user set can be edited by everyone who has the access rights. An owner has
	to be added to every stock item in order to use the ownership control.

### Owner: Group vs User

There are two types of owners in InvenTree: [groups](../settings/permissions.md#group) and [users](../settings/permissions.md#user).

* If a group is selected as owner, **all** users linked to the specified group will be able to edit the stock location or item.
* If a user is selected as owner, only the specified user will be able to edit the stock location or item.

When selecting an owner, in the drop-down list, groups are annotated with the <span class='fas fa-users'></span> icon and users are annotated with the <span class='fas fa-user'></span> icon:

{% with id="stock_owner_type", url="stock/stock_owner_type.png", description="Display stock owner type" %}
{% include 'img.html' %}
{% endwith %}

### Set Stock Location Owner

To specify the owner of a stock location, navigate to the stock location detail page. Click on the <span class='fas fa-sitemap'></span> icon under the location's name then click on "Edit Location".

!!! warning
	If you cannot see the <span class='fas fa-sitemap'></span> icon, it means that you do **not** have permissions to edit stock locations. Refer to [the permissions documentation](../settings/permissions.md#roles) and/or contact your InvenTree administrator.

In the "Edit Stock Location" form, select the owner and click the "Submit" button:

{% with id="stock_location_owner", url="stock/stock_location_owner.png", description="Set stock location owner" %}
{% include 'img.html' %}
{% endwith %}

Setting the owner of stock location will automatically:

* Set the owner of all children locations to the same owner.
* Set the owner of all stock items at this location to the same owner.

The inherited ownership changes with stock transfer. If a stock item is transferred from a location
owned by Daniel to a location owned by Peter the owner of the stock item and the access right will
also change from Daniel to Peter. This is only valid for the inherited ownership. If a stock item
is directly owned by Peter the ownership and the access right will stay with Peter even when the item
is moved to a location owned by Daniel.

!!! info
	If the owner of a children location or a stock item is a subset of the specified owner (eg. a user linked to the specified group), the owner won't be updated.

### Set Stock Item Owner

To specify the owner of a stock item, navigate to the stock item detail page. Click on the <span class='fas fa-tools'></span> icon under the item's name then click on "Edit stock item".

!!! warning
	If you cannot see the <span class='fas fa-tools'></span> icon, it means that you do **not** have permissions to edit stock items. Refer to [the permissions documentation](../settings/permissions.md/#roles) and/or contact your InvenTree administrator.

In the "Edit Stock Item" form, select the owner and click the "Save" button:

{% with id="stock_item_owner", url="stock/stock_item_owner.png", description="Set stock item owner" %}
{% include 'img.html' %}
{% endwith %}
