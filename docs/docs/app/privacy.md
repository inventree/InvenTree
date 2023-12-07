---
title: Privacy Statement
---

## InvenTree App Privacy Policy

The InvenTree mobile app requires some extra permissions for complete functionality. Additionally, some user information is stored locally on the device where the app is installed.

## Data Collection

### User Profiles

For each *profile* configured in the app, the following information is stored locally on the device:

- Server name (e.g. "InvenTree Demo")
- Server address (e.g. "https://demo.inventree.org)
- *API token*

#### User Authentication

The InvenTree app uses an API token for user authentication. This token is requested once from the server, and then stored locally on the device.

To initially request the token, the user will be required to enter their username and password.

!!! info "Password Storage"
    The user's username and password are not stored locally, or used for any purpose other than requesting an API token

#### Token Handling

A separate API token is stored locally for each profile. This token can be deleted at any time from within the app settings - this will force the user to enter their login credentials again to request a new token.

Additionally, the stored token may be revoked by the server, or expire. Either situation will again require the user to re-enter their username and password.

### Camera Permissions

The InvenTree app requires permission to access the device camera for the following purposes:

- Scanning barcode data
- Taking pictures with the device camera for upload to connected InvenTree server

Pictures taken in the InvenTree app are not stored or distributed to any other services.

## Personal Information

The InvenTree app does not collect any information which could be used to personally identify the user(s) of the device onto which the app is installed.

## Third Party Access

The InvenTree app does not share any personal information on users of the app with any third parties.

## Error Logs

The InvenTree app makes use of the [sentry.io](https://sentry.io/) service to monitor the app for bugs and run-time errors. When an error occurs in the app, log data is uploaded to the sentry server, where InvenTree developers can use this information to improve the quality of the app.

!!! question "Identifying Information"
    The uploaded error reports contain information on the nature of the error / bug; i.e. "where" in the app code the failures occurred. The uploaded data does not contain any information which can be used to identify users or extract user data.

!!! tip "Disable Error Reporting"
    If desired, users can disable error reporting entirely, from within the [app settings](./settings.md). This prevents any error logs from being uploaded to the sentry server.
