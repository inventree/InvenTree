---
title: Global Settings
---

## Global Settings

InvenTree ships with a lot of dynamic settings which can be configured at run-time. These settings are stored in the InvenTree database itself.

The following settings are *global* settings which affect all users.

!!! info "Staff Status Required"
    Only users with *staff* status can view and edit global settings

To edit global settings, select *Settings* from the menu in the top-right corner of the screen.

Global settings are arranged in the following categories:

### Server Settings

Configuration of basic server settings.

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| InvenTree Instance Name | String | String descriptor for the InvenTree server instance | InvenTree Server |
| Use Instance Name | Boolean | Use instance name in title bars | False |
| Restrict showing `about` | Boolean | Show the `about` modal only to superusers | False |
| Base URL | String | Base URL for server instance | *blank* |
| Company Name | String | Company name | My company name |
| Download from URL | Boolean | Allow downloading of images from remote URLs | False |

### Login Settings

Change how logins, password-forgot, signups are handled.

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Enable registration | Boolean | Enable self-registration for users on the login-pages | False |
| Enable SSO | Boolean | Enable SSO on the login-pages | False |
| Enable SSO registration | Boolean | Enable self-registration for users via SSO on the login-pages | False |
| Enable password forgot | Boolean | Enable password forgot function on the login-pages.<br><br>This will let users reset their passwords on their own. For this feature to work you need to configure E-mail | True |
| E-Mail required | Boolean | Require user to supply e-mail on signup.<br><br>Without a way (e-mail) to contact the user notifications and security features might not work! | False |
| Enforce MFA | Boolean | Users must use multifactor security.<br><br>This forces each user to setup MFA and use it on each authentication | False |
| Mail twice | Boolean | On signup ask users twice for their mail | False |
| Password twice | Boolean | On signup ask users twice for their password | True |
| Auto-fill SSO users | Boolean | Automatically fill out user-details from SSO account-data.<br><br>If this feature is enabled the user is only asked for their username, first- and surname if those values can not be gathered from their SSO profile. This might lead to unwanted usernames bleeding over. | True |
| Allowed domains | String | Restrict signup to certain domains (comma-separated, starting with @) |  |


### Barcodes

Configuration of barcode functionality

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Barcode Support | Boolean | Enable barcode functionality in web interface | True |

### Currencies

Configuration of currency support

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Default Currency | Currency | Default currency | USD |

### Reporting

Configuration of report generation

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Enable Reports | Boolean | Enable report generation | False |
| Page Size | String | Default page size | A4 |
| Debug Mode | Boolean | Generate reports in debug mode (HTML output) | False |
| Test Reports | Boolean | Enable generation of test reports | False |

### Parts

#### Main Settings

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| IPN Regex | String | Regular expression pattern for matching Part IPN | *blank* |
| Allow Duplicate IPN | Boolean | Allow multiple parts to share the same IPN | True |
| Allow Editing IPN | Boolean | Allow changing the IPN value while editing a part | True |
| Part Name Display Format | String | Format to display the part name | {% raw %}`{{ part.id if part.id }}{{ ' | ' if part.id }}{{ part.name }}{{ ' | ' if part.revision }}{{ part.revision if part.revision }}`{% endraw %} |
| Show Price History | Boolean | Display historical pricing for Part | False |
| Show Price in Forms | Boolean | Display part price in some forms | True |
| Show Price in BOM | Boolean | Include pricing information in BOM tables | True |
| Show related parts | Boolean | Display related parts for a part | True |
| Create initial stock | Boolean | Create initial stock on part creation | True |

#### Creation Settings

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Template | Boolean | Parts are templates by default | False |
| Assembly | Boolean | Parts can be assembled from other components by default | False |
| Component | Boolean | Parts can be used as sub-components by default | True |
| Trackable | Boolean | Parts are trackable by default | False |
| Purchaseable | Boolean | Parts are purchaseable by default | True |
| Salable | Boolean | Parts are salable by default | False |
| Virtual | Boolean | Parts are virtual by default | False |

#### Copy Settings

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Copy Part BOM Data | Boolean | Copy BOM data by default when duplicating a part | True |
| Copy Part Parameter Data | Boolean | Copy parameter data by default when duplicating a part | True |
| Copy Part Test Data | Boolean | Copy test data by default when duplicating a part | True |
| Copy Category Parameter Templates | Boolean | Copy category parameter templates when creating a part | True |

#### Internal Price Settings

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Internal Prices | Boolean | Enable internal prices for parts | False |
| Internal Price as BOM-Price | Boolean | Use the internal price (if set) in BOM-price calculations | False |

#### Part Import Setting

This section of the part settings allows staff users to:

- import parts to InvenTree clicking the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> Import Part</span> button
- enable the ["Import Parts" tab in the part category view](../part/part.md#part-import).

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Show Import in Views | Boolean | Display the import wizard in some part views | True |

#### Part Parameter Templates

Refer to the section describing [how to create part parameter templates](../part/parameter.md#create-template).

### Categories

In this section of the settings, staff users can set a list of parameters associated to a part category.

To add a parameter to a part category:

1. select the category in the dropdown list
2. click the <span class="badge inventree add"><span class='fas fa-plus-circle'></span> New Parameter</span> button on the top right
3. fill out the "Create Category Parameter Template" form
4. click the <span class="badge inventree confirm">Submit</span> button.

After a list of parameters is added to a part category and upon creation of a new part in this category, this list of parameters will be added by default to the new part.

### Stock

Configuration of stock item options

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Stock Expiry | Boolean | Enable stock expiry functionality | False |
| Stock Stale Time | Days | Number of days stock items are considered stale before expiring | 90 |
| Sell Expired Stock | Boolean | Allow sale of expired stock | False |
| Build Expired Stock | Boolean | Allow building with expired stock | False |
| Stock Ownership Control | Boolean | Enable ownership control functionality | False |

### Build Orders

Options for build orders

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Reference Pattern | String | Pattern for defining Build Order reference values | {% raw %}BO-{ref:04d}{% endraw %} |

### Purchase Orders

Options for purchase orders

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Reference Pattern | String | Pattern for defining Purchase Order reference values | {% raw %}PO-{ref:04d}{% endraw %} |

### Sales orders

Options for sales orders

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Reference Pattern | String | Pattern for defining Sales Order reference values | {% raw %}SO-{ref:04d}{% endraw %} |

### Plugin Settings

Change into what parts plugins can integrate into.

| Setting | Type | Description | Default |
| --- | --- | --- | --- |
| Enable URL integration | Boolean | Enable plugins to add URL routes | False |
| Enable navigation integration | Boolean | Enable plugins to integrate into navigation | False |
| Enable setting integration | Boolean | Enable plugins to integrate into inventree settings | False |
| Enable app integration | Boolean | Enable plugins to add apps | False |
