---
title: InvenTree Multi Factor Authentication
---

## Multi Factor Authentication

 InvenTree gives the option to use TOTP or statically generated backup tokens as an additional factor to password or SSO authentication. This is a widely adopted security feature on enterprise web services. We highly encourage to enable it if you expose your instance to the public internet.

As TOTP is an [open standard](https://datatracker.ietf.org/doc/html/rfc6238) there are a lot of different ways to hold your key and generate the time based tokens needed for authentication. That ranges from physical devices to password managers and mobile apps. We do not advertise any method but recommend to keep password and token generator separate from each other.

### Configuration

To make MFA mandatory for all users:

1. Enable it in the [global settings](../settings/global.md).

### Security Consideration

A user can lock themself out if they lose access to both the device with their TOTP app and their backup tokens. An admin can delete their tokens from the admin pages (they exist under the 'TOTP devices' / 'static devices' models) . This should be a last resort and only done by people knowledgeable about the [admin pages](../settings/admin.md) as changes there might circumvent InvneTrees business and security logic.
