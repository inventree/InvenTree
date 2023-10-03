"""Custom tasks associated with the plugin infrastructure."""

import datetime
import logging

from InvenTree.tasks import ScheduledTask, scheduled_task

logger = logging.getLogger('inventree')


@scheduled_task(ScheduledTask.DAILY)
def cleanup_old_plugin_configs():
    """Remove old plugin configuration entries which have not been updated recently."""

    from .models import PluginConfig

    threshold = datetime.datetime.now().date() - datetime.timedelta(days=30)

    # Delete plugin configs which have not been updated recently
    configs = PluginConfig.objects.filter(last_updated__lt=threshold)

    if configs.count() > 0:
        logger.info("Deleting %s old plugin configurations", configs.count())

        for config in configs:
            if config.is_builtin:
                logger.debug("Cannot delete builtin plugin config '%s'", config.key)
                continue

            if config.is_sample:
                logger.debug("Cannot delete sample plugin config '%s'", config.key)
                continue

            logger.debug("- Deleting plugin config '%s'", config.key)
            config.delete()
