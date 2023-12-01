"""Tests for state transition mechanism."""

from InvenTree.unit_test import InvenTreeTestCase

from .transition import StateTransitionMixin, TransitionMethod, storage


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

        class MyPrivateError(NotImplementedError):
            ...

        class ValidImplementation(TransitionMethod):
            def transition(self, *args, **kwargs):
                raise MyPrivateError('This is a private error for teting purposes')

        # Ensure registering works
        self.assertEqual(len(storage.list), 0)
        storage.collect()
        self.assertEqual(len(storage.list), 1)

        # Ensure the class is registered
        self.assertIn(ValidImplementation, storage.list)

        # Ensure stuff is passed to the class
        with self.assertRaises(MyPrivateError):
            def dflt(*args, **kwargs):
                print(args, kwargs)
            StateTransitionMixin.handle_transition(0, 1, self, ValidImplementation.transition, dflt)
