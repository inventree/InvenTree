"""Background task definitions for the 'machine' app."""

import structlog
from opentelemetry import trace

from common.settings import get_global_setting
from InvenTree.tasks import ScheduledTask, scheduled_task
from machine import registry

tracer = trace.get_tracer(__name__)
logger = structlog.get_logger('inventree')


@tracer.start_as_current_span('ping_machines')
@scheduled_task(ScheduledTask.MINUTES, 5)
def ping_machines():
    """Periodically ping all configured machines to check if they are online."""
    if not get_global_setting('MACHINE_PING_ENABLED', True):
        return

    for driver in registry.get_drivers():
        logger.debug("Pinging machines for driver '%s'", driver.SLUG)
        driver.ping_machines()
