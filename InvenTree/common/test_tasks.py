
# -*- coding: utf-8 -*-
from django.test import TestCase
from datetime import timedelta, datetime

from common.models import NotificationEntry
from InvenTree.tasks import offload_task


class TaskTest(TestCase):
    """
    Tests for common tasks
    """

    def test_delete(self):
        
        self.assertEqual(NotificationEntry.objects.all().count(), 0)
        # check empty run
        offload_task('common.tasks.delete_old_notifications',)

        # add a new tasks
        strat_data = datetime.now()
        NotificationEntry.objects.create(key='part.notify_low_stock', uid=1)
        late = NotificationEntry.objects.create(key='part.notify_low_stock', uid=2)
        late.updated = (strat_data - timedelta(days=90))
        late.save()
        later = NotificationEntry.objects.create(key='part.notify_low_stock', uid=3)
        later.updated = (strat_data - timedelta(days=95))
        later.save()

        self.assertEqual(NotificationEntry.objects.all().count(), 3)

        # run again and check that old notifications were deleted
        offload_task('common.tasks.delete_old_notifications',)
        self.assertEqual(NotificationEntry.objects.all().count(), 1)
