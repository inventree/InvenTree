---
title: InvenTree Demo
---

## InvenTree Demo

If you are interested in trying out InvenTree, you can access the InvenTree demo instance at [https://demo.inventree.org](https://demo.inventree.org).

This page is populated with a sample dataset, which is reset every 24 hours.

You can read more about the InvenTree demo here: [https://inventree.org/demo.html](https://inventree.org/demo.html)

### User Accounts

The demo instance has a number of user accounts which you can use to explore the system:

| Username | Password | Staff Access | Enabled | Description |
| -------- | -------- | ------------ | ------- | ----------- |
| noaccess | youshallnotpass | No | Yes | Can login, but has no permissions |
| allaccess | nolimits | No | Yes | View / create / edit all pages and items |
| reader | readonly | No | Yes | Can view all pages but cannot create, edit or delete database records |
| engineer | partsonly | No | Yes | Can manage parts, view stock, but no access to purchase orders or sales orders |
| steven | wizardstaff | Yes | Yes | Staff account, can access some admin sections |
| ian | inactive | No | No | Inactive account, cannot log in |
| susan | inactive | No | No | Inactive account, cannot log in |
| admin | inventree | Yes | Yes | Superuser account, can access all parts of the system |

### Dataset

The demo instance is populated with a sample dataset, which is reset every 24 hours.

The source data used in the demo instance can be found on our [GitHub page](https://github.com/inventree/demo-dataset).

### Local Setup

If you wish to install the demo dataset locally (for initial testing), you can run the following command (via [invoke](./start/invoke.md)):

```bash
invoke dev.setup-test -i
```

*(Note: The command above may be slightly different if you are running in docker.)*

This will install the demo dataset into your local InvenTree instance.

!!! warning "Warning"
    This command will **delete all existing data** in your InvenTree instance! It is not intended to be used on a production system, or loaded into an existing dataset.

### Clear Data

To clear demo data from your instance, and start afresh with a clean database, you can run the following command (via [invoke](./start/invoke.md)):

```bash
invoke dev.delete-data
```

!!! warning "Warning"
    This command will **delete all existing data** in your InvenTree instance, including any data that you have added yourself.
