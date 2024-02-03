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
    """Base label printing driver."""

    machine_type = 'label_printer'

    # Run printing functions by default in a background worker.
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
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer
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
            printing_options: The printing options set for this print job defined in the PrintingOptionsSerializer
                by default the following options are available:
                - copies: number of copies to print for each label

        Returns:
            If USE_BACKGROUND_WORKER=False, a JsonResponse object which indicates outcome to the user, otherwise None

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
            request: The django request used to make the get printers request
        """
        return cast(list['LabelPrintingMachineType'], self.get_machines())

    def get_printing_options_serializer(
        self, request: Request, *args, **kwargs
    ) -> 'BaseLabelPrintingDriver.BasePrintingOptionsSerializer':
        """Return a serializer class instance with dynamic printing options.

        Arguments:
            request: The request made to print a label or interfering the available serializer fields via an OPTIONS request
            *args, **kwargs: need to be passed to the serializer instance

        Returns:
            A class instance of a DRF serializer class, by default this an instance of
            self.PrintingOptionsSerializer using the *args, **kwargs if existing for this driver
        """
        serializer = getattr(self, 'PrintingOptionsSerializer', None)

        if not serializer:
            return BaseLabelPrintingDriver.BasePrintingOptionsSerializer(
                *args, **kwargs
            )  # type: ignore

        return serializer(*args, **kwargs)

    # --- helper functions
    @property
    def machine_plugin(self) -> LabelPrintingMixin:
        """Returns the builtin machine label printing plugin."""
        plg = plg_registry.get_plugin('inventreelabelmachine')
        return cast(LabelPrintingMixin, plg)

    def render_to_pdf(
        self, label: LabelTemplate, item: LabelItemType, request: Request, **kwargs
    ) -> HttpResponse:
        """Render this label to PDF format.

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
        """Render this label to PDF and return it as bytes.

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
        """Render this label to HTML format.

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
        """Render this label to PNG format.

        Arguments:
            label: The LabelTemplate object to render
            item: The item to render the label with
            request: The HTTP request object which triggered this print job

        Keyword Arguments:
            pdf_data: The pdf document as bytes (optional)
            dpi: The dpi used to render the image (optional)
        """
        label.object_to_print = item
        png = self.machine_plugin.render_to_png(label, request, **kwargs)
        label.object_to_print = None
        return png

    required_overrides = [[print_label, print_labels]]

    class BasePrintingOptionsSerializer(serializers.Serializer):
        """Printing options base serializer that implements common options."""

        copies = serializers.IntegerField(
            default=1,
            label=_('Copies'),
            help_text=_('Number of copies to print for each label'),
        )


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

    class LabelPrinterStatus(MachineStatus):
        """Label printer status codes."""

        CONNECTED = 100, _('Connected'), 'success'
        STANDBY = 101, _('Standby'), 'success'
        PRINTING = 110, _('Printing'), 'primary'
        LABEL_SPOOL_EMPTY = 301, _('Label spool empty'), 'warning'
        DISCONNECTED = 400, _('Disconnected'), 'danger'

    MACHINE_STATUS = LabelPrinterStatus

    default_machine_status = LabelPrinterStatus.DISCONNECTED

    @property
    def location(self):
        """Access the machines location instance using this property."""
        location_pk = self.get_setting('LOCATION', 'M')

        if not location_pk:
            return None

        return StockLocation.objects.get(pk=location_pk)
