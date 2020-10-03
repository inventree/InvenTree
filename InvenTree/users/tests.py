# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase

from users.models import RuleSet


class RuleSetModelTest(TestCase):
    """
    Some simplistic tests to ensure the RuleSet model is setup correctly.
    """

    def test_ruleset_models(self):

        keys = RuleSet.RULESET_MODELS.keys()
        
        # Check if there are any rulesets which do not have models defined

        missing = [name for name in RuleSet.RULESET_NAMES if name not in keys]

        if len(missing) > 0:
            print("The following rulesets do not have models assigned:")
            for m in missing:
                print("-", m)

        # Check if models have been defined for a ruleset which is incorrect
        extra = [name for name in keys if name not in RuleSet.RULESET_NAMES]

        if len(extra) > 0:
            print("The following rulesets have been improperly added to RULESET_MODELS:")
            for e in extra:
                print("-", e)

        # Check that each ruleset has models assigned
        empty = [key for key in keys if len(RuleSet.RULESET_MODELS[key]) == 0]

        if len(empty) > 0:
            print("The following rulesets have empty entries in RULESET_MODELS:")
            for e in empty:
                print("-", e)

        self.assertEqual(len(missing), 0)
        self.assertEqual(len(extra), 0)
        self.assertEqual(len(empty), 0)

