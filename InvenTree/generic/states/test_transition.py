"""Tests for state transition mechanism."""

from InvenTree.unit_test import InvenTreeTestCase

from .transition import StateTransitionMixin, TransitionMethod, storage


class MyPrivateError(NotImplementedError):
    """Error for testing purposes."""


def dflt(*args, **kwargs):
    """Default function for testing."""
    raise MyPrivateError('dflt')


class TransitionTests(InvenTreeTestCase):
    """Tests for basic NotificationMethod."""

    def test_class(self):
        """Ensure that the class itself works."""

        class ErrorImplementation(TransitionMethod):
            ...

        with self.assertRaises(NotImplementedError):
            ErrorImplementation()

    def test_storage(self):
        """Ensure that the storage collection mechanism works."""

        class RaisingImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                raise MyPrivateError('RaisingImplementation')

        # Ensure registering works
        self.assertEqual(len(storage.list), 0)
        storage.collect()
        self.assertEqual(len(storage.list), 3)

        # Ensure the class is registered
        self.assertIn(RaisingImplementation, storage.list)

        # Ensure stuff is passed to the class
        with self.assertRaises(MyPrivateError) as exp:
            StateTransitionMixin.handle_transition(0, 1, self, self, dflt)
        self.assertEqual(str(exp.exception), 'RaisingImplementation')

    def test_default_function(self):
        """Ensure that the default function is called."""

        class ValidImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                return False  # Return false to indicate that this should run

        # Ensure the default action is called
        with self.assertRaises(MyPrivateError) as exp:
            StateTransitionMixin.handle_transition(0, 1, self, self, dflt)
        self.assertEqual(str(exp.exception), 'dflt')
