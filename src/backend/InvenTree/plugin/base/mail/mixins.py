"""Plugin mixin class for mails."""

from django.core.mail import EmailMessage

from plugin import PluginMixinEnum
from plugin.helpers import MixinNotImplementedError


class MailMixin:
    """Mixin that provides support for processing mails before/after going to the sending/receiving commands.

    Implementing classes must provide a "process_mail_out" and "process_mail_in" function:
    """

    def process_mail_out(self, mail: EmailMessage, *args, **kwargs) -> None:
        """Function to handle a mail that is going to be send.

        Must be overridden by plugin.
        """
        # Default implementation does not do anything
        raise MixinNotImplementedError

    def process_mail_in(self, mail: EmailMessage, *args, **kwargs) -> None:
        """Function to handle a mail that was received.

        Must be overridden by plugin.
        """
        # Default implementation does not do anything
        raise MixinNotImplementedError

    class MixinMeta:
        """Meta options for this mixin."""

        MIXIN_NAME = 'Mail'

    def __init__(self):
        """Register the mixin."""
        super().__init__()
        self.add_mixin(PluginMixinEnum.MAIL, True, __class__)
