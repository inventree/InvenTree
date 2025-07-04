# Changelog

All notable changes to this project will be documented in this file (starting with 1.0.0).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - yyyy-mm-dd (in UTC)

### Added

### Changed

### Removed


## [Unreleased - 1.0.0 ] - 2025-07-xx

The first "stable" release following semver but not extensively other than the previous releases. The use of 1.0 indicates the stability that users already expect from InvenTree.

An overarching theme of this release is the complete switch to a new UI framework and paradigm (PUI). The old templating based UI (CUI) is now removed. This makes major improvements in the security and portability of InvenTree possible.

Our blog holds [a few articles](https://inventree.org/blog/2024/09/23/ui-roadmap) on the topic. This journey started in [March 2022](https://github.com/inventree/InvenTree/issues/2789) and was announced [in 2023](https://inventree.org/blog/2023/08/28/react).

### Added


### Changed


### Removed

## [0.14.0] - 2024-02-29

#### General

This release focused on furthering PUI, improving the API and enhancing the developer tooling.

We added machine integration, a feature that allows the user to connect more than 1 printer of the same manufacturer and model to an instance. It also enables integration of other machines, it is planned to develop this feature further in the next releases. This feature is PUI-only. [#6486](https://github.com/inventree/InvenTree/issues/6486)

A few quality of life improvements were made to the CI, such as the addition of API schema tracking, which ensures API versions are tracked and documented. We switched to ruff for CI linting, uv for installing packages and updated to the 4.2 LTS version of Django.

PUI was developed further, with the addition of support for SSO, user registration, and greatly improved tables among many additions. Especially administrative functions are improved compared to the classical UI (CUI).

PUI is enabled by default in this release and can be accessed by navigating to `/platform/` on the instance. We appreciate feedback.

### Added

- Machine model and integration https://github.com/inventree/InvenTree/pull/4824
- Disabling plugin installation from the web interface/API (https://github.com/inventree/InvenTree/issues/6531)
- Importing part image names https://github.com/inventree/InvenTree/pull/6513
- Support for Engineering units https://github.com/inventree/InvenTree/pull/6539
- Blocking outputs if tests not successful https://github.com/inventree/InvenTree/pull/6057
- API schema tracking https://github.com/inventree/InvenTree/pull/6440
- API documentation on the doc site https://github.com/inventree/InvenTree/pull/6319
- Wider Validation plugin support https://github.com/inventree/InvenTree/pull/6410
- Support for SSO in PUI https://github.com/inventree/InvenTree/pull/6333
- Translation support for tables in PUI https://github.com/inventree/InvenTree/pull/6357
- Slovak support https://github.com/inventree/InvenTree/pull/6351
- User Registration for PUI https://github.com/inventree/InvenTree/pull/6309
- Creating user with password from file https://github.com/inventree/InvenTree/pull/6144
- OpenAPI tracing https://github.com/inventree/InvenTree/pull/6211

### Fixed

- SITE_URL missdetection (https://github.com/inventree/InvenTree/pull/6585)
- Wrong rendering of temperatures (https://github.com/inventree/InvenTree/pull/6584)
- Maintenance mode problems https://github.com/inventree/InvenTree/pull/6422
- News Feed timeouts blocking the server https://github.com/inventree/InvenTree/pull/6250
- Importing data with owners https://github.com/inventree/InvenTree/pull/6271

### Changed

- Switched from Django 3 LTS to 4.2 LTS https://github.com/inventree/InvenTree/pull/6173
- Switched to psycog >3 https://github.com/inventree/InvenTree/pull/6573
- Switched from django-allauth 0.59.0 to  https://github.com/inventree/InvenTree/pull/6301
- Switched to uv for install (expermintal) https://github.com/inventree/InvenTree/pull/6499
- Switched to ruff for CI linnting https://github.com/inventree/InvenTree/pull/6167

### Removed

- Django-debug-toolbar https://github.com/inventree/InvenTree/pull/6196


## Old releases

Release notes are available https://docs.inventree.org/en/stable/releases/release_notes/
