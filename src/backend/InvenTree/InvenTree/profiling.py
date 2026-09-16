"""Helper functions for profiling InvenTree code.

A set of decorators to assist with profiling functions and logging,
which implement oft-repeated patterns used during development and debugging.

Note: These functions are not to be used in production code.
"""

from functools import wraps


def ensure_debug():
    """Ensure that InvenTree is running in DEBUG mode."""
    from django.conf import settings

    if not settings.DEBUG:
        raise RuntimeError('Profiling functions can only be used in DEBUG mode!')


def time_function(func):  # pragma: no cover
    """Decorator to time a function's execution duration.

    Args:
        func: Function to be timed
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        import time

        ensure_debug()

        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()

        duration = end_time - start_time
        print(f"Function '{func.__name__}' executed in {duration:.6f} seconds.")

        return result

    return wrapper


def profile_function(filename='profile.prof'):  # pragma: no cover
    """Decorator to profile a function using cProfile.

    Args:
        func: Function to be profiled
        filename: Output filename for the profiling data
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            import cProfile
            import io
            import pstats

            ensure_debug()

            pr = cProfile.Profile()
            pr.enable()

            result = func(*args, **kwargs)

            pr.disable()
            s = io.StringIO()
            sortby = pstats.SortKey.CUMULATIVE
            ps = pstats.Stats(pr, stream=s).sort_stats(sortby)
            ps.dump_stats(filename)
            print(s.getvalue())

            return result

        return wrapper

    return decorator


def log_slow_queries(
    threshold: float = 0.01, n: int = 5, log_to_file: bool = True
):  # pragma: no cover
    """Decorator to log slow database queries in a Django view function.

    Args:
        func: Function to be decorated
        threshold: Time threshold (in seconds) for logging slow queries
        n: Number of slowest queries to log
        log_to_file: Whether to log to a file or print to console
    """

    def decorator(func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            from django.db import connection

            ensure_debug()

            result = func(*args, **kwargs)

            slow_queries = [
                q for q in connection.queries if float(q.get('time', 0)) >= threshold
            ]
            slow_queries.sort(key=lambda x: float(x.get('time', 0)), reverse=True)

            log_entries = []
            for query in slow_queries[:n]:
                log_entry = f'Time: {query["time"]}s | SQL: {query["sql"]}'
                log_entries.append(log_entry)

            if log_entries:
                log_message = '\n'.join(log_entries)
                if log_to_file:
                    with open('slow_queries.log', 'w', encoding='utf-8') as f:
                        f.write(f'Slow queries detected:\n{log_message}\n')
                else:
                    print(f'Slow queries detected:\n{log_message}')

            return result

        return wrapper

    return decorator


# Raise an exception if this file is imported outside of DEBUG mode
ensure_debug()
