"""Configuration settings specific to a particular database backend."""

from pathlib import Path

import structlog

from InvenTree.config import get_boolean_setting, get_config_value, get_setting

logger = structlog.get_logger('inventree')


def get_db_backend():
    """Return the database backend configuration."""
    # For the core database configuration values, we test for UPPERCASE configuration values as a backup,
    # due to legacy reasons (original config files were uppercase,
    # but we moved to lowercase for consistency with other settings.

    db_config = {
        'ENGINE': get_setting(
            'INVENTREE_DB_ENGINE', 'database.engine', '', typecast=str
        )
        or get_config_value('database.ENGINE'),
        'NAME': get_setting('INVENTREE_DB_NAME', 'database.name', '', typecast=str)
        or get_config_value('database.NAME'),
        'USER': get_setting('INVENTREE_DB_USER', 'database.user', '', typecast=str)
        or get_config_value('database.USER'),
        'PASSWORD': get_setting(
            'INVENTREE_DB_PASSWORD', 'database.password', '', typecast=str
        )
        or get_config_value('database.PASSWORD'),
        'HOST': get_setting('INVENTREE_DB_HOST', 'database.host', '', typecast=str)
        or get_config_value('database.HOST'),
        'PORT': get_setting('INVENTREE_DB_PORT', 'database.port', '', typecast=str)
        or get_config_value('database.PORT'),
        'OPTIONS': get_setting(
            'INVENTREE_DB_OPTIONS', 'database.options', {}, typecast=dict
        )
        or get_config_value('database.OPTIONS')
        or {},
    }

    # Check for required keys
    required_keys = ['ENGINE', 'NAME']

    for key in required_keys:
        if not db_config[key]:
            raise ValueError(
                f'Missing required database configuration key: INVENTREE_DB_{key}'
            )

    DB_ENGINE = db_config['ENGINE'].lower()

    # Correct common misspelling
    if DB_ENGINE == 'sqlite':
        DB_ENGINE = 'sqlite3'  # pragma: no cover

    if DB_ENGINE in ['sqlite3', 'postgresql', 'mysql']:
        # Prepend the required python module string
        DB_ENGINE = f'django.db.backends.{DB_ENGINE}'
        db_config['ENGINE'] = DB_ENGINE

    if 'sqlite' in DB_ENGINE:
        db_name = str(Path(db_config['NAME']).resolve())
        db_config['NAME'] = db_name

    logger.info('DB_ENGINE: %s', DB_ENGINE)
    logger.info('DB_NAME: %s', db_config['NAME'])
    logger.info('DB_HOST: %s', db_config.get('HOST', "''"))

    # Set testing options for the database
    db_config['TEST'] = {'CHARSET': 'utf8'}

    # Set collation option for mysql test database
    if 'mysql' in DB_ENGINE:
        db_config['TEST']['COLLATION'] = 'utf8_general_ci'  # pragma: no cover

    # Specify database specific configuration
    set_db_options(DB_ENGINE, db_config['OPTIONS'])

    return db_config


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
        raise ValueError(f'Unknown database engine: {engine}')


def set_postgres_options(db_options: dict):
    """Set database options specific to postgres backend."""
    from django.db.backends.postgresql.psycopg_any import IsolationLevel

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
    # issue to resolve itself.  If that doesn't happen, whatever happened
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
    # protect against simultaneous changes.
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
    import InvenTree.ready

    # Specify minimum timeout behavior for SQLite connections
    if 'timeout' not in db_options:
        db_options['timeout'] = int(
            get_setting('INVENTREE_DB_TIMEOUT', 'database.timeout', 10)
        )

    # Specify the transaction mode for the database
    # For the backend worker thread, IMMEDIATE mode is used,
    # it has been determined to provide better protection against database locks in the worker thread
    db_options['transaction_mode'] = (
        'IMMEDIATE' if InvenTree.ready.isInWorkerThread() else 'DEFERRED'
    )

    # SQLite's default isolation level is Serializable due to SQLite's
    # single writer implementation.  Presumably as a result of this, it is
    # not possible to implement any lower isolation levels in SQLite.
    # https://www.sqlite.org/isolation.html

    if get_boolean_setting('INVENTREE_DB_WAL_MODE', 'database.wal_mode', True):
        # Specify that we want to use Write-Ahead Logging (WAL) mode for SQLite databases, as this allows for better concurrency and performance
        db_options['init_command'] = 'PRAGMA journal_mode=WAL;'
