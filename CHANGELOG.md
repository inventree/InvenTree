# Changelog

All notable changes to this project will be documented in this file (starting with 1.0.0).

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - yyyy-mm-dd (in UTC)

### Added

- Added `order_queryset` report helper function in [#10439](https://github.com/inventree/InvenTree/pull/10439)
- Added `SupplierMixin` to import data from suppliers in [#9761](https://github.com/inventree/InvenTree/pull/9761)
- Added much more detailed status information for machines to the API endpoint (including backend and frontend changes) in [#10381](https://github.com/inventree/InvenTree/pull/10381)
- Added ability to partially complete and partially scrap build outputs in [#10499](https://github.com/inventree/InvenTree/pull/10499)
- Added support for Redis ACL user-based authentication in [#10551](https://github.com/inventree/InvenTree/pull/10551)
- Expose stock adjustment forms to the UI plugin context in [#10584](https://github.com/inventree/InvenTree/pull/10584)
- Allow stock adjustments for "in production" items in [#10600](https://github.com/inventree/InvenTree/pull/10600)

### Changed

- Changed site URL check to allow protocol mismatches if `INVENTREE_SITE_LAX_PROTOCOL` is set to `True` (default) in [#10454](https://github.com/inventree/InvenTree/pull/10454)
- Changed call signature of `get_global_setting` to use `environment_key` instead of `enviroment_key` in [#10557](https://github.com/inventree/InvenTree/pull/10557)

### Removed


## [1.0.0 ] - 2025-09-15

The first "stable" release following semver but not extensively other than the previous releases. The use of 1.0 indicates the stability that users already expect from InvenTree.

An overarching theme of this release is the complete switch to a new UI framework and paradigm (PUI). The old templating based UI (CUI) is now removed. This makes major improvements in the security and portability of InvenTree possible.

Our blog holds [a few articles](https://inventree.org/blog/2024/09/23/ui-roadmap) on the topic. This journey started in [March 2022](https://github.com/inventree/InvenTree/issues/2789) and was announced [in 2023](https://inventree.org/blog/2023/08/28/react).


Specific entries to the changelog will be kept for all stable channel minor releases, for changes in 1.0 please refer to the [blog posts](https://inventree.org/blog/2025/09/15/1.0.0) and the [milestone](https://github.com/inventree/InvenTree/milestone/17)
