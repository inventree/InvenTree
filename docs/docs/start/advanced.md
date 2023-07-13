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


## Authentication

### LDAP

You can link your InvenTree server to an LDAP server. If you run the docker image, everything required is already installed. For bare metal installs, first install the required system packages that are needed for the `python-ldap` pip package, then install the python packages manually:

```bash
apt install build-essential python3-dev libldap2-dev libsasl2-dev
source ./env/bin/activate  # dont forget to source the venv before installing via pip
pip install python-ldap django-auth-ldap
```

Next you can start configuring the connection. Either use the config file or set the environment variables.

| config key | ENV Variable | Description |
| --- | --- | --- |
| `ldap.enabled` | `INVENTREE_LDAP_ENABLED` | Set this to `True` to enable LDAP. |
| `ldap.server_uri` | `INVENTREE_LDAP_SERVER_URI` | LDAP Server URI, e.g. `ldap://example.org` |
| `ldap.bind_dn` | `INVENTREE_LDAP_BIND_DN` | LDAP bind dn, e.g. `cn=admin,dc=example,dc=org` |
| `ldap.bind_password` | `INVENTREE_LDAP_BIND_PASSWORD` | LDAP bind password |
| `ldap.search_base_dn` | `INVENTREE_LDAP_SEARCH_BASE_DN` | LDAP search base dn, e.g. `cn=Users,dc=example,dc=org` |
| `ldap.search_filter_str`| `INVENTREE_LDAP_SEARCH_FILTER_STR` | LDAP search filter str, default: `uid=%(user)s` |
| `ldap.user_attr_map` | `INVENTREE_LDAP_USER_ATTR_MAP` | LDAP <-> Inventree user attribute map, can be json if used as env, in yml directly specify the object. default: `{"first_name": "givenName", "last_name": "sn", "email": "mail"}` |
| `ldap.always_update_user` | `INVENTREE_LDAP_ALWAYS_UPDATE_USER` | Always update the user on each login, default: `true` |
| `ldap.cache_timeout` | `INVENTREE_LDAP_CACHE_TIMEOUT` | cache timeout to reduce traffic with LDAP server, default: `3600` (1h) |
