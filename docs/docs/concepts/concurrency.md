---
title: Database Concurrency
---

## Database Concurrency

InvenTree is a multi-user system, and it also runs [background tasks](../start/processes.md#background-worker) which modify the database. This means that the same database record can be changed by two processes at (almost) the same time - for example, a user edits a build order while a background task is completing the outputs of that same build order.

If this is not managed, one process can silently overwrite the changes made by the other (a "lost update"), as each process saves the data it read *before* the other process finished.

### How Contention is Managed

InvenTree relies on *row-level locking* in the database to prevent lost updates:

- **Editing an object:** When an existing object is updated via the API, the database row is locked *before* the object is read. The object is then validated and saved within a single database transaction, and the lock is released when the request completes.
- **Performing an action:** Actions against an existing object (e.g. issuing, completing or cancelling an order, completing build outputs, receiving items, assigning a barcode) are handled in the same way: the target object is locked for the duration of the request, and if the action fails then none of its changes are saved.
- **Background tasks:** Tasks which adjust quantities (e.g. completing build outputs, consuming allocated stock, receiving items) lock the rows they work on, and re-read the current values before changing them.

A request waits for a short time (around two seconds) for a lock to be released, which is long enough for most operations to complete without the user noticing. If the object is still locked after this time (e.g. a background task is processing a large number of items), the request is rejected with a `409 Conflict` response, and no changes are made. The request can safely be submitted again once the other process has finished.

In the user interface, this is displayed as an error message at the top of the form:

{{ image("start/contention_error.png", "Error message displayed when an item is locked by another process") }}

!!! tip "Try Again"
    This message does not indicate a problem with the data which was entered. Wait a few moments for the other process to complete, and then submit the form again.

### Where Failures Can Still Occur

Row-level locking prevents the most common lost updates, but it cannot cover every case:

- **Stale forms:** A lock is only held while a request is being processed, not while a form is open. If an object is changed by someone else after a form has been opened, submitting the form overwrites those changes with the (older) values displayed in the form.
- **Operations across many objects:** Operations which act on many objects at once (e.g. bulk stock adjustments) are not locked as a single unit. Two such operations which overlap may have to wait for each other, and one of them may fail.
- **Deadlocks:** If two processes each wait for a lock held by the other, the database aborts one of them. The aborted request (or background task) fails with an error, and its changes are not saved.
- **[Plugins](../plugins/index.md) and custom code:** Code which loads an object, modifies it and saves it without locking the row (e.g. a third-party plugin, or the admin interface) is not protected, and can overwrite a concurrent change. Plugin developers should refer to the [development guidelines](../plugins/develop.md#development-guidelines).
- **Serializable isolation:** If the [`INVENTREE_DB_ISOLATION_SERIALIZABLE`](../start/config.md#postgresql-settings) option is enabled, the database itself rejects any transaction which conflicts with another. Data is never silently overwritten in this mode, but InvenTree does not automatically retry a rejected transaction: a request or background task which conflicts with another fails with a server error, and must be retried manually.

### SQLite Limitations

SQLite does not support row-level locking - instead, the entire database is locked while a process is writing to it. As a result:

- The protections described above are **not available**. A concurrent edit can still overwrite changes made by another process.
- Only one process can write to the database at a time. A process which cannot obtain the database lock within the configured [`INVENTREE_DB_TIMEOUT`](../start/config.md#sqlite-settings) fails with a "database is locked" error.

This is one of the reasons that SQLite is not recommended for production use, particularly where multiple users (or a background worker) are active at the same time. Refer to the [SQLite limitations](../start/processes.md#sqlite-limitations) for more information. Use PostgreSQL or MySQL for any installation where data integrity is important.
