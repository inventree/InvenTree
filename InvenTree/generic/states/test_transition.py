"""Tests for state transition mechanism."""

from InvenTree.unit_test import InvenTreeTestCase

from .transition import StateTransitionMixin, TransitionMethod, storage


class MyPrivateError(NotImplementedError):
    """Error for testing purposes."""


def dflt(*args, **kwargs):
    """Default function for testing."""
    raise MyPrivateError('dflt')


def _clean_storage(refs):
    """Clean the storage."""
    for ref in refs:
        del ref
    storage.collect()


class TransitionTests(InvenTreeTestCase):
    """Tests for basic NotificationMethod."""

    def test_class(self):
        """Ensure that the class itself works."""

        class ErrorImplementation(TransitionMethod):
            ...

        with self.assertRaises(NotImplementedError):
            ErrorImplementation()

        _clean_storage([ErrorImplementation])

    def test_storage(self):
        """Ensure that the storage collection mechanism works."""

        class RaisingImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                raise MyPrivateError('RaisingImplementation')

        # Ensure registering works
        storage.collect()

        # Ensure the class is registered
        self.assertIn(RaisingImplementation, storage.list)

        # Ensure stuff is passed to the class
        with self.assertRaises(MyPrivateError) as exp:
            StateTransitionMixin.handle_transition(0, 1, self, self, dflt)
        self.assertEqual(str(exp.exception), 'RaisingImplementation')

        _clean_storage([RaisingImplementation])

    def test_function(self):
        """Ensure that a TransitionMethod's function is called."""

        # Setup
        class ValidImplementationNoEffect(TransitionMethod):
            def transition(self, *args, **kwargs):
                return False  # Return false to test that that work too

        class ValidImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                return 1234

        storage.collect()
        self.assertIn(ValidImplementationNoEffect, storage.list)
        self.assertIn(ValidImplementation, storage.list)

        # Ensure that the function is called
        self.assertEqual(StateTransitionMixin.handle_transition(0, 1, self, self, dflt), 1234)

        _clean_storage([ValidImplementationNoEffect, ValidImplementation])

    def test_default_function(self):
        """Ensure that the default function is called."""
        with self.assertRaises(MyPrivateError) as exp:
            StateTransitionMixin.handle_transition(0, 1, self, self, dflt)
        self.assertEqual(str(exp.exception), 'dflt')
