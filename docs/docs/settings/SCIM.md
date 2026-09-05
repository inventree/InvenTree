---
title: SCIM Provisioning
---

## SCIM Provisioning

InvenTree provides a SCIM 2.0 service provider endpoint, allowing an external Identity Providers such as Microsoft Entra ID (Azure AD) or Okta to automatically provision and deprovision users/groups.

!!! info "SSO is separate"
    SCIM handles provisioning (creating, updating and deactivating accounts). Login via external Identity Providers ([Single Sign-On](./SSO.md)) is a separate process and settings.

### Supported Operations

The InvenTree SCIM endpoint implements a simple SCIM server as per [RFC7643](https://www.rfc-editor.org/rfc/rfc7643). So discovery and simple users / groups actions are enabled.

Users are _deactivated_ rather than deleted when removed via SCIM.

Bulk operations and more advanced HTTP features are not supported. This approach might not scale to thousands of users.

### Authentication

The SCIM endpoint is **not** authenticated against InvenTree user accounts, OAuth2, or API tokens. Instead, a single bearer secret is generated from the Admin Center and used by your Identity Provider to authenticate every SCIM request:

InvenTree does not store the raw secret - only a HMAC-SHA256 digest of it (seeded with the server's `SECRET_KEY`) is persisted to the database. This means:

- A stolen database backup cannot be used to reconstruct or replay the SCIM secret.
- Rotating the server's `SECRET_KEY` invalidates any previously generated SCIM secret.
- If you lose the secret you need to generate a new one.

!!! warning "Still very powerful"
    The SCIM secret gives full access to create, update and deactivate users and groups. Keep it secret, and rotate it if you suspect it has been compromised.

### Enable SCIM Provisioning

1. Open the [Admin Center](./admin.md#admin-center) and navigate to *Identity > SCIM*. This pane is only visible to admins / superusers.
2. Click *Enable SCIM* to generate the bearer secret. The secret is displayed for the only time - copy it immediately.
3. Copy the *Base URL* shown in the same pane (this is your InvenTree instance's SCIM endpoint, e.g. `https://your-instance/scim/v2/`).
4. In your Identity Provider's SCIM application configuration, enter the Base URL as the *SCIM base URL*, and the copied secret as the *Bearer Token* / *API Token*.
5. Trigger a test connection from your Identity Provider to ensure everything was copied correctly

### Rotating or Disabling

- **Rotate Secret**: generates a new secret. The Identity Provider side must be updated
- **Disable SCIM**: disables the endpoint and revokes the current secret

### Limitations

- Only a single Identity Provider is supported at a time - do not register multiple clients at the same time
- The SCIM filter grammar is minimal (`attribute eq "value"` only). Complex filter expressions are not supported as of now
