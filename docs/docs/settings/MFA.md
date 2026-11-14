---
title: InvenTree Multi Factor Authentication
---

## Multi Factor Authentication

 InvenTree gives the option to use [TOTP](https://en.wikipedia.org/wiki/Time-based_One-Time_Password) or statically generated backup tokens as an additional factor to password or SSO authentication. This is a widely adopted security feature on enterprise web services. We highly encourage to enable it if you expose your instance to the public internet.

As TOTP is an [open standard](https://datatracker.ietf.org/doc/html/rfc6238) there are a lot of different ways to hold your key and generate the time based tokens needed for authentication. That ranges from physical devices to password managers and mobile apps. We do not advertise any method but recommend to keep password and token generator separate from each other.

### Configuration

To make MFA mandatory for all users:

1. Enable it in the [global settings](../settings/global.md).

### Email Verification

Setting up MFA requires a verified email address. Users created by an administrator start with an unverified address; completing the password reset from their welcome email verifies it, after which they can set up MFA on first login.

If a user's email address is still unverified (for example, if their account has more than one address), the MFA setup page offers to resend the verification email. As a last resort, an admin can mark the address as verified in the [Database Admin interface](../settings/db_admin.md) (*Accounts* → *Email addresses*).

### Security Consideration

Password based [basic authentication](../api/index.md#basic-auth) against the API is refused for users with MFA configured, and for all users while MFA is enforced. API clients should use tokens (generated in the user interface) or OAuth2 instead.

While MFA is enforced:

- Users without MFA must set it up before they can use the web interface or API with their session.
- [API tokens](../api/index.md#tokens) cannot be requested until MFA is set up.
- Existing API tokens of users without MFA are refused. They are not deleted, and work again once the user sets up MFA.

Enabling enforcement ends all existing user sessions immediately.

API tokens are bearer credentials: a valid token is not challenged for a second factor on each request. Users with MFA configured can only request a token via the API shortly after logging in (including their second factor). Treat tokens like passwords and revoke any that may have been exposed. Administrators who enable enforcement on an existing instance should review the issued tokens in the [Admin Center](../settings/admin.md#admin-center).

A user can lock themselves out if they lose access to both the device with their TOTP app and their backup tokens. An admin can delete their tokens from the Database Admin interface (they exist under the 'TOTP devices' / 'static devices' models). This should be a last resort and only done by people knowledgeable about the [Database Admin interface](../settings/db_admin.md), as changes there might circumvent InvenTree's business and security logic.
