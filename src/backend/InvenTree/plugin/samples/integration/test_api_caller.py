"""Unit tests for action caller sample."""

from django.test import TestCase

from plugin import registry


class SampleApiCallerPluginTests(TestCase):
    """Tests for SampleApiCallerPluginTests."""

    def test_return(self):
        """Check if the external api call works."""
        import time

        # The plugin should be defined
        self.assertIn('sample-api-caller', registry.plugins)
        plg = registry.plugins['sample-api-caller']
        self.assertTrue(plg)

        # do an api call
        # Note: rate limits may apply in CI
        result = False

        for _i in range(5):
            result = plg.get_external_url()
            if result:
                break
            else:
                time.sleep(1)

        self.assertTrue(result)
        self.assertIn('data', result)
