---
title: Experimental Features
---

## Feature Flags

InvenTree ships with django-flags and enables path (parameter), user, session, date or settings based feature flags. This allows admins to slowly test and roll out new features on their instance without running parallel instances.

Additional flags can be provided via the the `INVENTREE_FLAGS` environment key (see [configuration](../start/config.md#environment-variables)).

Superusers can configure run-time conditions [as per django-flags](https://cfpb.github.io/django-flags/conditions/) docs under `/admin/flags/flagstate/`.

## Current Experimental Features

| Feature | Key | Description |
| --- | --- | --- |
| oAuth provider / api | OIDC | Use oAuth and OIDC to authenticate users with the API - [read more](../api/index.md#oauth2--oidc) |
