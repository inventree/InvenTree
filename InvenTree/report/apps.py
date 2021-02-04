import os
import shutil
import logging

from django.apps import AppConfig
from django.conf import settings


logger = logging.getLogger(__name__)


class ReportConfig(AppConfig):
    name = 'report'

    def ready(self):
        """
        This function is called whenever the report app is loaded
        """

        self.create_default_test_reports()

    def create_default_test_reports(self):
        """
        Create database entries for the default TestReport templates,
        if they do not already exist
        """

        try:
            from .models import TestReport
        except:
            # Database is not ready yet
            return

        src_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates',
            'report',
        )

        dst_dir = os.path.join(
            settings.MEDIA_ROOT,
            'report',
            'inventree',  # Stored in secret directory!
            'test',
        )

        if not os.path.exists(dst_dir):
            logger.info(f"Creating missing directory: '{dst_dir}'")
            os.makedirs(dst_dir, exist_ok=True)

        # List of test reports to copy across
        reports = [
            {
                'file': 'inventree_test_report.html',
                'name': 'InvenTree Test Report',
                'description': 'Stock item test report',
            },
        ]

        for report in reports:

            # Create destination file name
            filename = os.path.join(
                'report',
                'inventree',
                'test',
                report['file']
            )

            src_file = os.path.join(src_dir, report['file'])
            dst_file = os.path.join(settings.MEDIA_ROOT, filename)

            if not os.path.exists(dst_file):
                logger.info(f"Copying test report template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            try:
                # Check if a report matching the template already exists
                if TestReport.objects.filter(template=filename).exists():
                    continue

                logger.info(f"Creating new TestReport for '{report['name']}'")

                TestReport.objects.create(
                    name=report['name'],
                    description=report['description'],
                    template=filename,
                    filters='',
                    enabled=True
                )
            except:
                pass
