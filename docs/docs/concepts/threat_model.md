---
title: Threat Model
---

## Threat Model

Deploying InvenTree to production requires to knowledge of the security assumptions and threat model of the underlying system. This document outlines the security assumptions and threat model of InvenTree as a software. It is assumed that the system that InvenTree is deployed on top of is configured following best practices and is trusted.

## Assumed Trust

1. The InvenTree server is only available to trusted networks and there are detection mechanisms in place to detect unauthorised access.

    1. When exposing to the internet, it is recommended to use a WAF and ensure only trusted IP ranges are allowed to access the server
    2. It is recommended to enforce usage of strong traffic encryption along the network path
    3. Authentication attempts are rate limited by InvenTree but should be monitored with appropriate monitoring and alerting solutions to detect long-running brute force attacks

2. All users are trusted - therefore user uploaded files can be assumed to be safe. There are basic checks in place to ensure that the files are not using common attack vectors but those are not exhaustive.

3. Superuser permissions are only given to trusted users and not used for daily operations. A superuser account can manipulate or extract all files on the server that the InvenTree server process have access to.

4. All templates and plugins are trusted.

    1. It is recommended to only use plugins and templates from trusted sources.
    2. It is recommended to review the code of the plugins and templates before using them.
    3. Templates and plugins can access all files that the server and worker processes have access to
    4. Plugins can access the inventree database and all data in the database
    5. Plugins can access all environment variables that are accessible to the server and worker processes

## Possible Attack Vectors

1. Malicious plugins or templates can overwrite or delete files on the server, bypass security checks, or leak sensitive information.
2. Token phishing attacks can be used to impersonate users. Tokens are not scoped to specific IPs or devices. Limit their usage and use lowest possible user permissions.
3. Malicious file uploads. Attachments are served (by default) under the same domain as the backend - this can lead to XSS attacks.

There are various checks to gate against common attack vectors but above vectors are explicitly not addressed as they require organisational policies and procedures to mitigate.

## Secure Development Cycle

The InvenTree project is developed following best practices. Read more in the [project security guide](../security.md).
