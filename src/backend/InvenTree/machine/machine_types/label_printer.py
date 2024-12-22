"""Label printing machine type."""

from typing import Union, cast

from django.contrib.auth.models import AnonymousUser
from django.db import models
from django.db.models.query import QuerySet
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _

from PIL.Image import Image
from rest_framework import serializers
from rest_framework.request import Request

from generic.states import ColorEnum
from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus
from plugin import registry as plg_registry
from plugin.base.label.mixins import LabelPrintingMixin
from report.models import LabelTemplate
from stock.models import StockLocation


class LabelPrinterBaseDriver(BaseDriver):
    """Base driver for label printer machines.

    Attributes:
        USE_BACKGROUND_WORKER (bool): If True, the `print_label()` and `print_labels()` methods will be run in a background worker (default: True)
    """

    machine_type = 'label-printer'

    USE_BACKGROUND_WORKER = True

    def print_label(
        self,
        machine: 'LabelPrinterMachine',
        label: LabelTemplate,
        item: models.Model,
        **kwargs,
    ) -> None:
        """Print a single label with the provided template and item.

        Arguments:
            machine: The LabelPrintingMachine instance that should be used for printing
            label: The LabelTemplate object to use for printing
            item: The database item to print (e.g. StockItem instance)

        Keyword Arguments:
            printing_options (dict): The printing options set for this print job defined in the PrintingOptionsSerializer
                by default the following options are available:
                - copies: number of copies to print for the label

        Note that the supplied args/kwargs may be different if the driver overrides the print_labels() method.
        """

    def print_labels(
        self,
        machine: 'LabelPrinterMachine',
        label: LabelTemplate,
        items: QuerySet[models.Model],
        **kwargs,
    ) -> Union[None, JsonResponse]:
        """Print one or more labels with the provided template and items.

        Arguments:
            machine: The LabelPrintingMachine instance that should be used for printing
            label: The LabelTemplate object to use for printing
            items: The list of database items to print (e.g. StockItem instances)

        Keyword Arguments:
            printing_options (dict): The printing options set for this print job defined in the PrintingOptionsSerializer
                by default the following options are available:
                - copies: number of copies to print for each label

        Returns:
            If `USE_BACKGROUND_WORKER=False`, a JsonResponse object which indicates outcome to the user, otherwise None

        The default implementation simply calls print_label() for each label, producing multiple single label output "jobs"
        but this can be overridden by the particular driver.
        """
        for item in items:
            self.print_label(machine, label, item, **kwargs)

    def get_printers(
        self, label: LabelTemplate, items: QuerySet, **kwargs
    ) -> list['LabelPrinterMachine']:
        """Get all printers that would be available to print this job.

        By default all printers that are initialized using this driver are returned.

        Arguments:
            label: The LabelTemplate object to use for printing
            items: The lost of database items to print (e.g. StockItem instances)

        Keyword Arguments:
            request (Request): The django request used to make the get printers request
        """
        return cast(list['LabelPrinterMachine'], self.get_machines())

    def get_printing_options_serializer(
        self, request: Request, *args, **kwargs
    ) -> 'LabelPrinterBaseDriver.PrintingOptionsSerializer':
        """Return a serializer class instance with dynamic printing options.

        Arguments:
            request: The request made to print a label or interfering the available serializer fields via an OPTIONS request

        Note:
            `*args`, `**kwargs` needs to be passed to the serializer instance

        Returns:
            A class instance of a DRF serializer class, by default this an instance of self.PrintingOptionsSerializer using the *args, **kwargs if existing for this driver
        """
        return self.PrintingOptionsSerializer(*args, **kwargs)  # type: ignore

    # --- helper functions
    @property
    def machine_plugin(self) -> LabelPrintingMixin:
        """Returns the builtin machine label printing plugin that manages printing through machines."""
        plg = plg_registry.get_plugin('inventreelabelmachine')
        return cast(LabelPrintingMixin, plg)

    def render_to_pdf(
        self, label: LabelTemplate, item: models.Model, **kwargs
    ) -> HttpResponse:
        """Helper method to render a label to PDF format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
        """
        request = self._get_dummy_request()
        return self.machine_plugin.render_to_pdf(label, item, request, **kwargs)

    def render_to_pdf_data(
        self, label: LabelTemplate, item: models.Model, **kwargs
    ) -> bytes:
        """Helper method to render a label to PDF and return it as bytes for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
        """
        return (
            self.render_to_pdf(label, item, **kwargs)
            .get_document()  # type: ignore
            .write_pdf()
        )

    def render_to_html(self, label: LabelTemplate, item: models.Model, **kwargs) -> str:
        """Helper method to render a label to HTML format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
        """
        request = self._get_dummy_request()
        return self.machine_plugin.render_to_html(label, item, request, **kwargs)

    def render_to_png(
        self, label: LabelTemplate, item: models.Model, **kwargs
    ) -> Union[Image, None]:
        """Helper method to render a label to PNG format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with

        Keyword Arguments:
            pdf_data (bytes): The pdf document as bytes (optional)
            dpi (int): The dpi used to render the image (optional)
            use_cairo (bool): Whether to use the pdftocairo backend for rendering which provides better results in tests,
                see [#6488](https://github.com/inventree/InvenTree/pull/6488) for details. If False, pdftoppm is used (default: True)
            pdf2image_kwargs (dict): Additional keyword arguments to pass to the
                [`pdf2image.convert_from_bytes`](https://pdf2image.readthedocs.io/en/latest/reference.html#pdf2image.pdf2image.convert_from_bytes) method (optional)
        """
        request = self._get_dummy_request()
        return self.machine_plugin.render_to_png(label, item, request, **kwargs)

    def _get_dummy_request(self):
        """Return a dummy request object to it work with legacy code.

        Note: this is a private method and can be removed at anytime
        """
        r = HttpRequest()
        r.META['SERVER_PORT'] = '80'
        r.META['SERVER_NAME'] = 'localhost'
        r.user = AnonymousUser()

        return r

    required_overrides = [[print_label, print_labels]]

    class PrintingOptionsSerializer(serializers.Serializer):
        """Printing options serializer that implements common options.

        This can be overridden by the driver to implement custom options, but the driver should always extend this class.

        Example:
            This example shows how to extend the default serializer and add a new option:
            ```py
            class MyDriver(LabelPrinterBaseDriver):
                # ...

                class PrintingOptionsSerializer(LabelPrinterBaseDriver.PrintingOptionsSerializer):
                    auto_cut = serializers.BooleanField(
                        default=True,
                        label=_('Auto cut'),
                        help_text=_('Automatically cut the label after printing'),
                    )
            ```
        """

        copies = serializers.IntegerField(
            default=1,
            label=_('Copies'),
            help_text=_('Number of copies to print for each label'),
        )


class LabelPrinterStatus(MachineStatus):
    """Label printer status codes.

    Attributes:
        CONNECTED: The printer is connected and ready to print
        UNKNOWN: The printer status is unknown (e.g. there is no active connection to the printer)
        PRINTING: The printer is currently printing a label
        NO_MEDIA: The printer is out of media (e.g. the label spool is empty)
        DISCONNECTED: The driver cannot establish a connection to the printer
    """

    CONNECTED = 100, _('Connected'), ColorEnum.success
    UNKNOWN = 101, _('Unknown'), ColorEnum.secondary
    PRINTING = 110, _('Printing'), ColorEnum.primary
    NO_MEDIA = 301, _('No media'), ColorEnum.warning
    PAPER_JAM = 302, _('Paper jam'), ColorEnum.warning
    DISCONNECTED = 400, _('Disconnected'), ColorEnum.danger


class LabelPrinterMachine(BaseMachineType):
    """Label printer machine type, is a direct integration to print labels for various items."""

    SLUG = 'label-printer'
    NAME = _('Label Printer')
    DESCRIPTION = _('Directly print labels for various items.')

    base_driver = LabelPrinterBaseDriver

    MACHINE_SETTINGS = {
        'LOCATION': {
            'name': _('Printer Location'),
            'description': _('Scope the printer to a specific location'),
            'model': 'stock.stocklocation',
        }
    }

    MACHINE_STATUS = LabelPrinterStatus

    default_machine_status = LabelPrinterStatus.UNKNOWN

    @property
    def location(self):
        """Access the machines location instance using this property."""
        location_pk = self.get_setting('LOCATION', 'M')

        if not location_pk:
            return None

        return StockLocation.objects.get(pk=location_pk)
