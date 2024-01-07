"""Tests for state transition mechanism."""

from InvenTree.unit_test import InvenTreeTestCase

from .transition import StateTransitionMixin, TransitionMethod, storage

# Global variables to determine which transition classes raises an exception
global raise_storage
global raise_function

raise_storage = False
raise_function = False


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

        global raise_storage
        global raise_function

        raise_storage = True
        raise_function = False

        class RaisingImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                """Custom transition method."""

                global raise_storage

                if raise_storage:
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

        global raise_storage
        global raise_function

        raise_storage = False
        raise_function = True

        # Setup
        class ValidImplementationNoEffect(TransitionMethod):
            def transition(self, *args, **kwargs):
                return False  # Return false to test that that work too

        class ValidImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):

                global raise_function

                if raise_function:
                    return 1234
                else:
                    return False

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
