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

Configuration of basic server settings:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("INVENTREE_BASE_URL") }}
{{ globalsetting("INVENTREE_COMPANY_NAME") }}
{{ globalsetting("INVENTREE_INSTANCE") }}
{{ globalsetting("INVENTREE_INSTANCE_TITLE") }}
{{ globalsetting("INVENTREE_INSTANCE_ID", default="Randomly generated value") }}
{{ globalsetting("INVENTREE_ANNOUNCE_ID") }}
{{ globalsetting("INVENTREE_RESTRICT_ABOUT") }}
{{ globalsetting("DISPLAY_FULL_NAMES") }}
{{ globalsetting("DISPLAY_PROFILE_INFO") }}
{{ globalsetting("INVENTREE_UPDATE_CHECK_INTERVAL") }}
{{ globalsetting("INVENTREE_DOWNLOAD_FROM_URL") }}
{{ globalsetting("INVENTREE_DOWNLOAD_IMAGE_MAX_SIZE") }}
{{ globalsetting("INVENTREE_DOWNLOAD_FROM_URL_USER_AGENT") }}
{{ globalsetting("INVENTREE_STRICT_URLS") }}
{{ globalsetting("INVENTREE_BACKUP_ENABLE") }}
{{ globalsetting("INVENTREE_BACKUP_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_TASKS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_ERRORS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_NOTIFICATIONS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_EMAIL_DAYS") }}
{{ globalsetting("INVENTREE_PROTECT_EMAIL_LOG") }}


### Login Settings

Change how logins, password-forgot, user registrations are handled:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("LOGIN_ENABLE_PWD_FORGOT") }}
{{ globalsetting("LOGIN_MAIL_REQUIRED") }}
{{ globalsetting("LOGIN_ENFORCE_MFA") }}
{{ globalsetting("LOGIN_ENABLE_REG") }}
{{ globalsetting("LOGIN_SIGNUP_MAIL_TWICE") }}
{{ globalsetting("LOGIN_SIGNUP_PWD_TWICE") }}
{{ globalsetting("SIGNUP_GROUP") }}
{{ globalsetting("LOGIN_SIGNUP_MAIL_RESTRICTION") }}
{{ globalsetting("LOGIN_ENABLE_SSO") }}
{{ globalsetting("LOGIN_ENABLE_SSO_REG") }}
{{ globalsetting("LOGIN_SIGNUP_SSO_AUTO") }}
{{ globalsetting("LOGIN_ENABLE_SSO_GROUP_SYNC") }}
{{ globalsetting("SSO_GROUP_MAP") }}
{{ globalsetting("SSO_GROUP_KEY") }}
{{ globalsetting("SSO_REMOVE_GROUPS") }}

#### Require User Email

If this setting is enabled, users must provide an email address when signing up. Note that some notification and security features require a valid email address.

#### Forgot Password

If this setting is enabled, users can reset their password via email. This requires a valid email address to be associated with the user account.

#### Enforce Multi-Factor Authentication

If this setting is enabled, users must have multi-factor authentication enabled to log in.

#### Auto Fill SSO Users

Automatically fill out user-details from SSO account-data. If this feature is enabled the user is only asked for their username, first- and surname if those values can not be gathered from their SSO profile. This might lead to unwanted usernames bleeding over.

### Barcodes

Configuration of barcode functionality:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("BARCODE_ENABLE") }}
{{ globalsetting("BARCODE_INPUT_DELAY") }}
{{ globalsetting("BARCODE_WEBCAM_SUPPORT") }}
{{ globalsetting("BARCODE_SHOW_TEXT") }}
{{ globalsetting("BARCODE_GENERATION_PLUGIN") }}
{{ globalsetting("BARCODE_STORE_RESULTS") }}
{{ globalsetting("BARCODE_RESULTS_MAX_NUM") }}

Read more about [barcode scanning](../barcodes/index.md).

### Pricing and Currency

Configuration of pricing data and currency support:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("INVENTREE_DEFAULT_CURRENCY") }}
{{ globalsetting("CURRENCY_CODES") }}
{{ globalsetting("CURRENCY_UPDATE_PLUGIN") }}
{{ globalsetting("CURRENCY_UPDATE_INTERVAL") }}
{{ globalsetting("PRICING_DECIMAL_PLACES_MIN") }}
{{ globalsetting("PRICING_DECIMAL_PLACES") }}
{{ globalsetting("PRICING_AUTO_UPDATE") }}
{{ globalsetting("PRICING_UPDATE_DAYS") }}

#### Part Pricing

Configuration of part pricing:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PART_INTERNAL_PRICE") }}
{{ globalsetting("PART_BOM_USE_INTERNAL_PRICE") }}
{{ globalsetting("PRICING_USE_SUPPLIER_PRICING") }}
{{ globalsetting("PRICING_PURCHASE_HISTORY_OVERRIDES_SUPPLIER") }}
{{ globalsetting("PRICING_USE_STOCK_PRICING") }}
{{ globalsetting("PRICING_STOCK_ITEM_AGE_DAYS") }}
{{ globalsetting("PRICING_USE_VARIANT_PRICING") }}
{{ globalsetting("PRICING_ACTIVE_VARIANTS") }}

### Reporting

Configuration of report generation:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("REPORT_ENABLE") }}
{{ globalsetting("REPORT_DEFAULT_PAGE_SIZE") }}
{{ globalsetting("REPORT_DEBUG_MODE") }}
{{ globalsetting("REPORT_LOG_ERRORS") }}

### Label Printing

Configuration of label printing:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("LABEL_ENABLE") }}
{{ globalsetting("LABEL_DPI") }}

### Parts

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PART_IPN_REGEX") }}
{{ globalsetting("PART_ALLOW_DUPLICATE_IPN") }}
{{ globalsetting("PART_ALLOW_EDIT_IPN") }}
{{ globalsetting("PART_ALLOW_DELETE_FROM_ASSEMBLY") }}
{{ globalsetting("PART_ENABLE_REVISION") }}
{{ globalsetting("PART_REVISION_ASSEMBLY_ONLY") }}
{{ globalsetting("PART_NAME_FORMAT") }}
{{ globalsetting("PART_SHOW_RELATED") }}
{{ globalsetting("PART_CREATE_INITIAL") }}
{{ globalsetting("PART_CREATE_SUPPLIER") }}
{{ globalsetting("PART_TEMPLATE") }}
{{ globalsetting("PART_ASSEMBLY") }}
{{ globalsetting("PART_COMPONENT") }}
{{ globalsetting("PART_TRACKABLE") }}
{{ globalsetting("PART_PURCHASEABLE") }}
{{ globalsetting("PART_SALABLE") }}
{{ globalsetting("PART_VIRTUAL") }}
{{ globalsetting("PART_COPY_BOM") }}
{{ globalsetting("PART_COPY_PARAMETERS") }}
{{ globalsetting("PART_COPY_TESTS") }}
{{ globalsetting("PART_CATEGORY_PARAMETERS") }}
{{ globalsetting("PART_CATEGORY_DEFAULT_ICON") }}

#### Parameter Templates

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PARAMETER_ENFORCE_UNITS") }}

For more information on parameters, refer to the [parameter documentation](../concepts/parameters.md).

### Categories

In this section of the settings, staff users can set a list of parameters associated to a part category.

To add a parameter to a part category:

1. Select the category in the dropdown list
2. Click the <span class="badge inventree add">{{ icon("plus-circle") }} New Parameter</span> button on the top right
3. Fill out the "Create Category Parameter Template" form
4. Click the <span class="badge inventree confirm">Submit</span> button.

After a list of parameters is added to a part category and upon creation of a new part in this category, this list of parameters will be added by default to the new part.

### Stock

Configuration of stock item options

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("SERIAL_NUMBER_GLOBALLY_UNIQUE") }}
{{ globalsetting("STOCK_DELETE_DEPLETED_DEFAULT") }}
{{ globalsetting("STOCK_BATCH_CODE_TEMPLATE") }}
{{ globalsetting("STOCK_ENABLE_EXPIRY") }}
{{ globalsetting("STOCK_STALE_DAYS") }}
{{ globalsetting("STOCK_ALLOW_EXPIRED_SALE") }}
{{ globalsetting("STOCK_ALLOW_EXPIRED_BUILD") }}
{{ globalsetting("STOCK_OWNERSHIP_CONTROL") }}
{{ globalsetting("STOCK_LOCATION_DEFAULT_ICON") }}
{{ globalsetting("STOCK_SHOW_INSTALLED_ITEMS") }}
{{ globalsetting("STOCK_ENFORCE_BOM_INSTALLATION") }}
{{ globalsetting("STOCK_ALLOW_OUT_OF_STOCK_TRANSFER") }}
{{ globalsetting("TEST_STATION_DATA") }}

### Build Orders

Refer to the [build order settings](../manufacturing/build.md#build-order-settings).

### Purchase Orders

Refer to the [purchase order settings](../purchasing/purchase_order.md#purchase-order-settings).

### Sales Orders

Refer to the [sales order settings](../sales/sales_order.md#sales-order-settings).

### Return Orders

Refer to the [return order settings](../sales/return_order.md#return-order-settings).

### Plugin Settings

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PLUGIN_ON_STARTUP") }}
{{ globalsetting("PLUGIN_UPDATE_CHECK") }}
{{ globalsetting("ENABLE_PLUGINS_URL") }}
{{ globalsetting("ENABLE_PLUGINS_NAVIGATION") }}
{{ globalsetting("ENABLE_PLUGINS_APP") }}
{{ globalsetting("ENABLE_PLUGINS_SCHEDULE") }}
{{ globalsetting("ENABLE_PLUGINS_EVENTS") }}
{{ globalsetting("ENABLE_PLUGINS_INTERFACE") }}
{{ globalsetting("ENABLE_PLUGINS_MAILS") }}

### Machine Settings

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("MACHINE_PING_ENABLED") }}

### Project Codes

Refer to the [project code settings](../concepts/project_codes.md).

## Override Global Settings

If desired, specific *global settings* can be overridden via environment variables or the configuration file.

Overriding a global setting will mark the setting as "read-only" in the user interface, and prevent it from being changed by user action. Additionally, the associated value stored in the database will be set to the value specified in the override.

Refer to the [configuration guide](../start/config.md#override-global-settings) for more information on how to override global settings.
