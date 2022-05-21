import logging
import os
import shutil

from django.apps import AppConfig
from django.conf import settings

from InvenTree.ready import canAppAccessDatabase

logger = logging.getLogger("inventree")


class ReportConfig(AppConfig):
    name = 'report'

    def ready(self):
        """
        This function is called whenever the report app is loaded
        """

        if canAppAccessDatabase(allow_test=True):
            self.create_default_test_reports()
            self.create_default_build_reports()

    def create_default_reports(self, model, reports):
        """
        Copy defualt report files across to the media directory.
        """

        # Source directory for report templates
        src_dir = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            'templates',
            'report',
        )

        # Destination directory
        dst_dir = os.path.join(
            settings.MEDIA_ROOT,
            'report',
            'inventree',
            model.getSubdir(),
        )

        if not os.path.exists(dst_dir):
            logger.info(f"Creating missing directory: '{dst_dir}'")
            os.makedirs(dst_dir, exist_ok=True)

        # Copy each report template across (if required)
        for report in reports:

            # Destination filename
            filename = os.path.join(
                'report',
                'inventree',
                model.getSubdir(),
                report['file'],
            )

            src_file = os.path.join(src_dir, report['file'])
            dst_file = os.path.join(settings.MEDIA_ROOT, filename)

            if not os.path.exists(dst_file):
                logger.info(f"Copying test report template '{dst_file}'")
                shutil.copyfile(src_file, dst_file)

            try:
                # Check if a report matching the template already exists
                if model.objects.filter(template=filename).exists():
                    continue

                logger.info(f"Creating new TestReport for '{report['name']}'")

                model.objects.create(
                    name=report['name'],
                    description=report['description'],
                    template=filename,
                    enabled=True
                )

            except:
                pass

    def create_default_test_reports(self):
        """
        Create database entries for the default TestReport templates,
        if they do not already exist
        """

        try:
            from .models import TestReport
        except:  # pragma: no cover
            # Database is not ready yet
            return

        # List of test reports to copy across
        reports = [
            {
                'file': 'inventree_test_report.html',
                'name': 'InvenTree Test Report',
                'description': 'Stock item test report',
            },
        ]

        self.create_default_reports(TestReport, reports)

    def create_default_build_reports(self):
        """
        Create database entries for the default BuildReport templates
        (if they do not already exist)
        """

        try:
            from .models import BuildReport
        except:  # pragma: no cover
            # Database is not ready yet
            return

        # List of Build reports to copy across
        reports = [
            {
                'file': 'inventree_build_order.html',
                'name': 'InvenTree Build Order',
                'description': 'Build Order job sheet',
            }
        ]

        self.create_default_reports(BuildReport, reports)
