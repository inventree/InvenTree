---
title: Advanced Topics
---

## Version Information

Starting with version 0.12 (and later), InvenTree includes more version information.

To view this information, navigate to the "About" page in the top menu bar and select "copy version information" on the bottom corner.

### Contained Information

The version information contains the following information extracted form the instance:

| Name | Always | Sample | Source |
| --- | --- | --- | --- |
| InvenTree-Version | Yes | 0.12.0 dev | instance |
| Django Version | Yes | 3.2.19 | instance |
| Commit Hash | No | aebff26 | environment: `INVENTREE_COMMIT_HASH`, git |
| Commit Date | No | 2023-06-10 | environment: `INVENTREE_COMMIT_DATE`, git |
| Commit Branch | No | master | environment: `INVENTREE_PKG_BRANCH`, git |
| Database | Yes | postgresql | environment: `INVENTREE_DB_*`, config: `database` - see [config](./config.md#database-options) |
| Debug-Mode | Yes | False | environment: `INVENTREE_DEBUG`, config: `config` - see [config](./config.md#basic-options) |
| Deployed using Docker | Yes | True | environment: `INVENTREE_DOCKER` |
| Platform | Yes | Linux-5.15.0-67-generic-x86_64 | instance |
| Installer | Yes | PKG | environment: `INVENTREE_PKG_INSTALLER`, instance |
| Target | No | ubuntu:20.04 | environment: `INVENTREE_PKG_TARGET` |
| Active plugins | Yes | [{'name': 'InvenTreeBarcode', 'slug': 'inventreebarcode', 'version': '2.0.0'}] | instance |


### Installer codes

The installer code is used to identify the way InvenTree was installed. If you vendor InvenTree, you can and should set the installer code to your own value to make sure debugging goes smoothly.

| Code | Description | Official |
| --- | --- | --- |
| PKG | Installed using a package manager | Yes |
| GIT | Installed using git | Yes |
| DOC | Installed using docker | Yes |
| DIO | Installed using digital ocean marketplace[^1] | No |

[^1]: Starting with fresh installs of 0.12.0 this code is set. Versions installed before 0.12.0 do not have this code set even after upgrading to 0.12.0.
