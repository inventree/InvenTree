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
{{ globalsetting("INVENTREE_DEFAULT_INTERNAL_COMPANY") }}
{{ globalsetting("INVENTREE_INSTANCE") }}
{{ globalsetting("INVENTREE_INSTANCE_TITLE") }}
{{ globalsetting("INVENTREE_INSTANCE_ID", default="Randomly generated value") }}
{{ globalsetting("INVENTREE_ANNOUNCE_ID") }}
{{ globalsetting("INVENTREE_LINK_PROOF") }}
{{ globalsetting("INVENTREE_SHOW_SUPERUSER_BANNER") }}
{{ globalsetting("INVENTREE_SHOW_ADMIN_BANNER") }}
{{ globalsetting("INVENTREE_RESTRICT_ABOUT") }}
{{ globalsetting("DISPLAY_FULL_NAMES") }}
{{ globalsetting("DISPLAY_PROFILE_INFO") }}
{{ globalsetting("WEEK_STARTS_ON") }}
{{ globalsetting("CALENDAR_HORIZON_MONTHS") }}
{{ globalsetting("INVENTREE_UPLOAD_MAX_SIZE") }}
{{ globalsetting("INVENTREE_STRICT_URLS") }}

Configuration of various scheduled tasks:

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("INVENTREE_UPDATE_CHECK_INTERVAL") }}
{{ globalsetting("INVENTREE_BACKUP_ENABLE") }}
{{ globalsetting("INVENTREE_BACKUP_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_TASKS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_ERRORS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_NOTIFICATIONS_DAYS") }}
{{ globalsetting("INVENTREE_DELETE_EMAIL_DAYS") }}
{{ globalsetting("INVENTREE_PROTECT_EMAIL_LOG") }}

#### Instance Identity

Each InvenTree server has an *instance ID*, which uniquely identifies that installation. It is a random UUID, generated automatically the first time it is needed and stored in the database. The following settings control how this identity is shared with other systems.

!!! warning "Keep the Instance ID Private"
    The instance ID is the shared secret behind [link proofs](#link-proof). Anyone who knows it can produce valid proofs for this server. Do not publish it unless you intend the server identity to be public.

##### Announce ID

If `INVENTREE_ANNOUNCE_ID` is enabled, the instance ID is included (as the `id` field) in the response of the `/api/` endpoint. This endpoint does not require authentication, so the ID becomes visible to anyone who can reach the server. If the setting is disabled (the default), the `id` field is `null`.

This setting can also be set with the `INVENTREE_ANNOUNCE_ID` environment variable.

!!! tip "Prefer Link Proofs"
    Announcing the ID also allows anyone to calculate link proofs for this server. If another system only needs to confirm that it is talking to a known server, leave this setting disabled and use a link proof instead.

##### Link Proof

A link proof allows another system to verify the identity of this server, *without* the instance ID being sent over the network. It is intended for a system which already knows the instance ID (for example, because it was shared out-of-band when the two systems were first linked), and wants to confirm that it is still talking to the same server.

If `INVENTREE_LINK_PROOF` is enabled (the default), a request to the `/api/` endpoint with a `link_nonce` query parameter returns a `link` value in the response:

```
GET /api/?link_nonce=<nonce>
```

- The nonce must be 1 to 64 characters long, and may contain only letters, digits, `-` and `_`.
- The verifying system should choose a new random nonce for each request.
- If link proofs are disabled, the nonce is invalid, or no instance ID exists yet, the `link` value is `null`.

The proof is calculated as follows:

1. A key is derived from the instance ID using HKDF-SHA256 (no salt, `info` = `inventree-link-v1`, 32 byte output).
2. An HMAC-SHA256 is calculated with this key, over the current month in UTC (formatted as `YYYY-MM`) followed by the nonce.
3. The proof is the first 32 characters of the hexadecimal digest.

The verifying system performs the same calculation with its copy of the instance ID, and checks that the result matches the returned `link` value. An example implementation in Python:

```python
import hashlib
import hmac
from datetime import datetime, timezone

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.hkdf import HKDF


def expected_proof(instance_id: str, nonce: str, epoch: str | None = None) -> str:
    """Calculate the expected link proof for a given instance ID and nonce."""
    if epoch is None:
        epoch = datetime.now(timezone.utc).strftime('%Y-%m')

    key = HKDF(
        algorithm=hashes.SHA256(), length=32, salt=None, info=b'inventree-link-v1'
    ).derive(instance_id.encode('utf-8'))

    message = (epoch + nonce).encode('utf-8')
    return hmac.new(key, message, hashlib.sha256).hexdigest()[:32]
```

!!! info "Month Boundaries"
    Because the proof includes the current month, a request made at the very end of a month may be answered with the next month's value (or the other way around). A verifier may also accept the proof for the adjacent month to allow for this.

This setting can also be set with the `INVENTREE_LINK_PROOF` environment variable, which takes precedence over the database value.


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
{{ globalsetting("REPORT_FETCH_URLS") }}
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
{{ globalsetting("PART_ENABLE_LOCKING") }}
{{ globalsetting("PART_ENABLE_REVISION") }}
{{ globalsetting("PART_REVISION_ASSEMBLY_ONLY") }}
{{ globalsetting("PART_NAME_FORMAT") }}
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
{{ globalsetting("PART_BOM_ALLOW_ZERO_QUANTITY") }}
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
{{ globalsetting("STOCK_ALLOW_EDIT_SERIAL") }}
{{ globalsetting("STOCK_ALLOW_DELETE_SERIALIZED") }}
{{ globalsetting("STOCK_DELETE_DEPLETED_DEFAULT") }}
{{ globalsetting("STOCK_BATCH_CODE_TEMPLATE") }}
{{ globalsetting("STOCK_ENABLE_EXPIRY") }}
{{ globalsetting("STOCK_STALE_DAYS") }}
{{ globalsetting("STOCK_ALLOW_EXPIRED_SALE") }}
{{ globalsetting("STOCK_ALLOW_EXPIRED_BUILD") }}
{{ globalsetting("STOCK_OWNERSHIP_CONTROL") }}
{{ globalsetting("STOCK_LOCATION_DEFAULT_ICON") }}
{{ globalsetting("STOCK_ENFORCE_BOM_INSTALLATION") }}
{{ globalsetting("STOCK_ALLOW_OUT_OF_STOCK_TRANSFER") }}
{{ globalsetting("STOCK_MERGE_ON_TRANSFER") }}
{{ globalsetting("TEST_STATION_DATA") }}

### Build Orders

Refer to the [build order settings](../manufacturing/build.md#build-order-settings).

### Purchase Orders

Refer to the [purchase order settings](../purchasing/purchase_order.md#purchase-order-settings).

### Sales Orders

Refer to the [sales order settings](../sales/sales_order.md#sales-order-settings).

### Return Orders

Refer to the [return order settings](../sales/return_order.md#return-order-settings).

### Transfer Orders

Refer to the [transfer order settings](../stock/transfer_order.md#transfer-order-settings).

### Plugin Settings

| Name | Description | Default | Units |
| ---- | ----------- | ------- | ----- |
{{ globalsetting("PLUGIN_ON_STARTUP") }}
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
