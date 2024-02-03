"""Label printing plugin that provides support for printing using a label printer machine."""

from typing import cast

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from rest_framework import serializers

from InvenTree.serializers import DependentField
from InvenTree.tasks import offload_task
from label.models import LabelTemplate
from machine.machine_types import BaseLabelPrintingDriver, LabelPrintingMachineType
from plugin import InvenTreePlugin
from plugin.machine import registry
from plugin.mixins import LabelPrintingMixin


def get_machine_and_driver(machine_pk: str):
    """Get the driver by machine pk and ensure that it is a label printing driver."""
    machine = registry.get_machine(machine_pk)

    if machine is None:
        return None, None

    if machine.SLUG != 'label_printer':
        return None, None

    machine = cast(LabelPrintingMachineType, machine)
    driver = machine.driver

    if driver is None:
        return machine, None

    return machine, cast(BaseLabelPrintingDriver, driver)


class InvenTreeLabelPlugin(LabelPrintingMixin, InvenTreePlugin):
    """Builtin plugin for machine label printing.

    This enables machines to print labels.
    """

    NAME = 'InvenTreeLabelMachine'
    TITLE = _('InvenTree machine label printer')
    DESCRIPTION = _('Provides support for printing using a machine')
    VERSION = '1.0.0'
    AUTHOR = _('InvenTree contributors')

    def print_labels(self, label: LabelTemplate, items, request, **kwargs):
        """Print labels implementation that calls the correct machine driver print_labels method."""
        machine, driver = get_machine_and_driver(
            kwargs['printing_options'].get('machine', '')
        )

        if driver is None or machine is None:
            return None

        print_kwargs = {
            **kwargs,
            'printing_options': kwargs['printing_options'].get('driver_options', {}),
        }

        if driver.USE_BACKGROUND_WORKER is False:
            return driver.print_labels(machine, label, items, request, **print_kwargs)

        offload_task(
            driver.print_labels, machine, label, items, request, **print_kwargs
        )

        return JsonResponse({
            'success': True,
            'message': f'{len(items)} labels printed',
        })

    class PrintingOptionsSerializer(serializers.Serializer):
        """Printing options serializer that adds a machine select and the machines options."""

        def __init__(self, *args, **kwargs):
            """Custom __init__ method to dynamically override the machine choices based on the request."""
            super().__init__(*args, **kwargs)

            view = kwargs['context']['view']
            template = view.get_object()
            items_to_print = view.get_items()

            machines: list[LabelPrintingMachineType] = []
            for driver in cast(
                list[BaseLabelPrintingDriver], registry.get_drivers('label_printer')
            ):
                machines.extend(
                    driver.get_printers(
                        template, items_to_print, request=kwargs['context']['request']
                    )
                )
            choices = [(m.pk, self.get_printer_name(m)) for m in machines]
            self.fields['machine'].choices = choices
            if len(choices) > 0:
                self.fields['machine'].default = choices[0][0]

        def get_printer_name(self, machine: LabelPrintingMachineType):
            """Construct the printers name."""
            name = machine.name

            if machine.location:
                name += f' @ {machine.location.name}'

            return name

        machine = serializers.ChoiceField(choices=[])

        driver_options = DependentField(
            depends_on=['machine'],
            field_serializer='get_driver_options',
            required=False,
        )

        def get_driver_options(self, fields):
            """Returns the selected machines serializer."""
            _, driver = get_machine_and_driver(fields['machine'])

            if driver is None:
                return None

            return driver.get_printing_options_serializer(
                self.context['request'], context=self.context
            )
