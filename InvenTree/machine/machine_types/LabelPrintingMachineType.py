"""Label printing machine type."""

from typing import Union, cast

from django.db.models.query import QuerySet
from django.http import HttpResponse, JsonResponse
from django.utils.translation import gettext_lazy as _

from PIL.Image import Image
from rest_framework import serializers
from rest_framework.request import Request

from label.models import LabelTemplate
from machine.machine_type import BaseDriver, BaseMachineType, MachineStatus
from plugin import registry as plg_registry
from plugin.base.label.mixins import LabelItemType, LabelPrintingMixin
from stock.models import StockLocation


class BaseLabelPrintingDriver(BaseDriver):
    """Base label printing driver.

    Attributes:
        USE_BACKGROUND_WORKER (bool): If True, the `print_label()` and `print_labels()` methods will be run in a background worker (default: True)
    """

    machine_type = 'label_printer'

    USE_BACKGROUND_WORKER = True

    def print_label(
        self,
        machine: 'LabelPrintingMachineType',
        label: LabelTemplate,
        item: LabelItemType,
        request: Request,
        **kwargs,
    ) -> None:
        """Print a single label with the provided template and item.

        Arguments:
            machine: The LabelPrintingMachine instance that should be used for printing
            label: The LabelTemplate object to use for printing
            item: The database item to print (e.g. StockItem instance)
            request: The HTTP request object which triggered this print job

        Keyword Arguments:
            printing_options (dict): The printing options set for this print job defined in the PrintingOptionsSerializer
                by default the following options are available:
                - copies: number of copies to print for the label

        Note that the supplied args/kwargs may be different if the driver overrides the print_labels() method.
        """
        pass

    def print_labels(
        self,
        machine: 'LabelPrintingMachineType',
        label: LabelTemplate,
        items: QuerySet[LabelItemType],
        request: Request,
        **kwargs,
    ) -> Union[None, JsonResponse]:
        """Print one or more labels with the provided template and items.

        Arguments:
            machine: The LabelPrintingMachine instance that should be used for printing
            label: The LabelTemplate object to use for printing
            items: The list of database items to print (e.g. StockItem instances)
            request: The HTTP request object which triggered this print job

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
            self.print_label(machine, label, item, request, **kwargs)

    def get_printers(
        self, label: LabelTemplate, items: QuerySet[LabelItemType], **kwargs
    ) -> list['LabelPrintingMachineType']:
        """Get all printers that would be available to print this job.

        By default all printers that are initialized using this driver are returned.

        Arguments:
            label: The LabelTemplate object to use for printing
            items: The lost of database items to print (e.g. StockItem instances)

        Keyword Arguments:
            request (Request): The django request used to make the get printers request
        """
        return cast(list['LabelPrintingMachineType'], self.get_machines())

    def get_printing_options_serializer(
        self, request: Request, *args, **kwargs
    ) -> 'BaseLabelPrintingDriver.PrintingOptionsSerializer':
        """Return a serializer class instance with dynamic printing options.

        Arguments:
            request: The request made to print a label or interfering the available serializer fields via an OPTIONS request

        Note:
            `*args`, `**kwargs` needs to be passed to the serializer instance

        Returns:
            A class instance of a DRF serializer class, by default this an instance of self.PrintingOptionsSerializer using the *args, **kwargs if existing for this driver
        """
        return self.PrintingOptionsSerializer(*args, **kwargs)

    # --- helper functions
    @property
    def machine_plugin(self) -> LabelPrintingMixin:
        """Returns the builtin machine label printing plugin that manages printing through machines."""
        plg = plg_registry.get_plugin('inventreelabelmachine')
        return cast(LabelPrintingMixin, plg)

    def render_to_pdf(
        self, label: LabelTemplate, item: LabelItemType, request: Request, **kwargs
    ) -> HttpResponse:
        """Helper method to render a label to PDF format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
            request: The HTTP request object which triggered this print job
        """
        label.object_to_print = item
        response = self.machine_plugin.render_to_pdf(label, request, **kwargs)
        label.object_to_print = None
        return response

    def render_to_pdf_data(
        self, label: LabelTemplate, item: LabelItemType, request: Request, **kwargs
    ) -> bytes:
        """Helper method to render a label to PDF and return it as bytes for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
            request: The HTTP request object which triggered this print job
        """
        return (
            self.render_to_pdf(label, item, request, **kwargs)
            .get_document()  # type: ignore
            .write_pdf()
        )

    def render_to_html(
        self, label: LabelTemplate, item: LabelItemType, request: Request, **kwargs
    ) -> str:
        """Helper method to render a label to HTML format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
            request: The HTTP request object which triggered this print job
        """
        label.object_to_print = item
        html = self.machine_plugin.render_to_html(label, request, **kwargs)
        label.object_to_print = None
        return html

    def render_to_png(
        self, label: LabelTemplate, item: LabelItemType, request: Request, **kwargs
    ) -> Image:
        """Helper method to render a label to PNG format for a specific item.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
            request: The HTTP request object which triggered this print job

        Keyword Arguments:
            pdf_data (bytes): The pdf document as bytes (optional)
            dpi (int): The dpi used to render the image (optional)
        """
        label.object_to_print = item
        png = self.machine_plugin.render_to_png(label, request, **kwargs)
        label.object_to_print = None
        return png

    required_overrides = [[print_label, print_labels]]

    class PrintingOptionsSerializer(serializers.Serializer):
        """Printing options serializer that implements common options.

        This can be overridden by the driver to implement custom options, but the driver should always extend this class.

        Example:
            This example shows how to extend the default serializer and add a new option:
            ```py
            class MyDriver(BaseLabelPrintingDriver):
                # ...

                class PrintingOptionsSerializer(BaseLabelPrintingDriver.PrintingOptionsSerializer):
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

    CONNECTED = 100, _('Connected'), 'success'
    UNKNOWN = 101, _('Unknown'), 'secondary'
    PRINTING = 110, _('Printing'), 'primary'
    NO_MEDIA = 301, _('No media'), 'warning'
    DISCONNECTED = 400, _('Disconnected'), 'danger'


class LabelPrintingMachineType(BaseMachineType):
    """Label printer machine type, is a direct integration to print labels for various items."""

    SLUG = 'label_printer'
    NAME = _('Label Printer')
    DESCRIPTION = _('Directly print labels for various items.')

    base_driver = BaseLabelPrintingDriver

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
