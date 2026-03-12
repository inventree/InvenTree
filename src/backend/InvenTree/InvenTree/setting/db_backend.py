"""Configuration settings specific to a particula rdatabase backend."""

import structlog

from InvenTree.config import get_boolean_setting, get_setting

logger = structlog.get_logger('inventree')


def set_db_options(engine: str, db_options: dict):
    """Update database options based on the specified database backend.

    Arguments:
        engine: The database engine (e.g. 'sqlite3', 'postgresql', etc.)
        db_options: The database options dictionary to update
    """
    logger.debug('Setting database options: %s', engine)

    if 'postgres' in engine:
        set_postgres_options(db_options)
    elif 'mysql' in engine:
        set_mysql_options(db_options)
    elif 'sqlite' in engine:
        set_sqlite_options(db_options)
    else:
        logger.warning('Unknown database engine: %s', engine)


def set_postgres_options(db_options: dict):
    """Set database options specific to postgres backend."""
    from django.db.backends.postgresql.psycopg_any import (  # type: ignore[unresolved-import]
        IsolationLevel,
    )

    # Connection timeout
    if 'connect_timeout' not in db_options:
        # The DB server is in the same data center, it should not take very
        # long to connect to the database server
        # # seconds, 2 is minimum allowed by libpq
        db_options['connect_timeout'] = int(
            get_setting('INVENTREE_DB_TIMEOUT', 'database.timeout', 2)
        )

    # Setup TCP keepalive
    # DB server is in the same DC, it should not become unresponsive for
    # very long. With the defaults below we wait 5 seconds for the network
    # issue to resolve itself.  It it that doesn't happen whatever happened
    # is probably fatal and no amount of waiting is going to fix it.
    # # 0 - TCP Keepalives disabled; 1 - enabled
    if 'keepalives' not in db_options:
        db_options['keepalives'] = int(
            get_setting('INVENTREE_DB_TCP_KEEPALIVES', 'database.tcp_keepalives', 1)
        )

    # Seconds after connection is idle to send keep alive
    if 'keepalives_idle' not in db_options:
        db_options['keepalives_idle'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_IDLE', 'database.tcp_keepalives_idle', 1
            )
        )

    # Seconds after missing ACK to send another keep alive
    if 'keepalives_interval' not in db_options:
        db_options['keepalives_interval'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_INTERVAL',
                'database.tcp_keepalives_interval',
                '1',
            )
        )

    # Number of missing ACKs before we close the connection
    if 'keepalives_count' not in db_options:
        db_options['keepalives_count'] = int(
            get_setting(
                'INVENTREE_DB_TCP_KEEPALIVES_COUNT',
                'database.tcp_keepalives_count',
                '5',
            )
        )

    # # Milliseconds for how long pending data should remain unacked
    # by the remote server
    # TODO: Supported starting in PSQL 11
    # "tcp_user_timeout": int(os.getenv("PGTCP_USER_TIMEOUT", "1000"),

    # Postgres's default isolation level is Read Committed which is
    # normally fine, but most developers think the database server is
    # actually going to do Serializable type checks on the queries to
    # protect against simultaneous changes.
    # https://www.postgresql.org/docs/devel/transaction-iso.html
    # https://docs.djangoproject.com/en/3.2/ref/databases/#isolation-level
    if 'isolation_level' not in db_options:
        serializable = get_boolean_setting(
            'INVENTREE_DB_ISOLATION_SERIALIZABLE', 'database.serializable', False
        )
        db_options['isolation_level'] = (
            IsolationLevel.SERIALIZABLE
            if serializable
            else IsolationLevel.READ_COMMITTED
        )


def set_mysql_options(db_options: dict):
    """Set database options specific to mysql backend."""
    # TODO TCP time outs and keepalives

    # MariaDB's default isolation level is Repeatable Read which is
    # normally fine, but most developers think the database server is
    # actually going to Serializable type checks on the queries to
    # protect against siumltaneous changes.
    # https://mariadb.com/kb/en/mariadb-transactions-and-isolation-levels-for-sql-server-users/#changing-the-isolation-level
    # https://docs.djangoproject.com/en/3.2/ref/databases/#mysql-isolation-level
    if 'isolation_level' not in db_options:
        serializable = get_boolean_setting(
            'INVENTREE_DB_ISOLATION_SERIALIZABLE', 'database.serializable', False
        )
        db_options['isolation_level'] = (
            'serializable' if serializable else 'read committed'
        )


def set_sqlite_options(db_options: dict):
    """Set database options specific to sqlite backend.

    References:
    - https://docs.djangoproject.com/en/5.0/ref/databases/#sqlite-notes
    - https://docs.djangoproject.com/en/6.0/ref/databases/#database-is-locked-errors
    """
    # Specify minimum timeout behavior for SQLite connections
    if 'timeout' not in db_options:
        db_options['timeout'] = int(
            get_setting('INVENTREE_DB_TIMEOUT', 'database.timeout', 10)
        )

    # Specify the transaction mode for the database
    # The default mode for SQLite is "DEFERRED"
    # However, in most cases it is preferable to use "IMMEDIATE"
    if 'transaction_mode' not in db_options:
        transaction_mode = str(
            get_setting(
                'INVENTREE_DB_TRANSACTION_MODE',
                'database.transaction_mode',
                'IMMEDIATE',
            )
        ).upper()

        if transaction_mode not in ['DEFERRED', 'IMMEDIATE', 'EXCLUSIVE']:
            raise ValueError(
                f"Specified database transaction mode '{transaction_mode}' is not a valid option."
            )

        db_options['transaction_mode'] = transaction_mode

    # SQLite's default isolation level is Serializable due to SQLite's
    # single writer implementation.  Presumably as a result of this, it is
    # not possible to implement any lower isolation levels in SQLite.
    # https://www.sqlite.org/isolation.html
