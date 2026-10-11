"""Integration tests for Cangxu inventory workflows."""

from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.urls import reverse
from django.utils import timezone

from openpyxl import Workbook

from build.models import Build
from build.validators import generate_next_build_reference
from company.models import Company, SupplierPart
from InvenTree.unit_test import InvenTreeAPITestCase
from order.models import (
    PurchaseOrder,
    PurchaseOrderLineItem,
    SalesOrder,
    SalesOrderAllocation,
    SalesOrderLineItem,
    SalesOrderShipment,
)
from part.models import BomItem, Part
from stock.models import StockItem, StockItemTracking, StockLocation
from stock.status_codes import StockHistoryCode, StockStatus

from .models import (
    CableEndDefinition,
    ConfigurationItem,
    CountSession,
    DataImportBatch,
    DataImportRecord,
    HardwareProfileRevision,
    ManufacturingLotStockItem,
    PartCodeAlias,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ShipmentManifest,
    UnitConfiguration,
)


class CangxuAPITestCase(InvenTreeAPITestCase):
    """Provide fixtures and permissions used by Cangxu API tests."""

    fixtures = [
        'category',
        'part',
        'location',
        'stock',
        'company',
        'test_templates',
        'bom',
    ]
    roles = [
        'build.add',
        'build.change',
        'part.add',
        'part.change',
        'purchase_order.add',
        'purchase_order.change',
        'return_order.add',
        'return_order.change',
        'sales_order.add',
        'sales_order.change',
        'stock.add',
        'stock.change',
    ]


class CangxuHardwareProfileTest(CangxuAPITestCase):
    """Exercise sourced multi-vendor hardware profiles and cable breakouts."""

    def test_switch_profile_tracks_chip_vendor_board_maker_and_ports(self):
        """Keep chipset vendor and board maker distinct and freeze approved data."""
        part = Part.objects.get(pk=25)
        chip_vendor = Company.objects.create(name='Synthetic Broadcom Chip Vendor')
        board_maker = Company.objects.create(name='Synthetic Linkreal Board Maker')
        profile = self.post(
            reverse('cangxu-hardware-profile-list'),
            {
                'part': part.pk,
                'revision': 'R1',
                'kind': HardwareProfileRevision.Kind.PCIE_SWITCH,
                'protocol': HardwareProfileRevision.Protocol.PCIE,
                'form_factor': HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                'chip_vendor': chip_vendor.pk,
                'board_manufacturer': board_maker.pk,
                'specifications': {'generation': 'PCIe 5.0', 'lane_count': 64},
                'source_reference': 'Synthetic engineering approval ENG-CX-001',
            },
            expected_code=201,
        )
        profile_id = profile.data['id']
        port = self.post(
            reverse('cangxu-hardware-port-list'),
            {
                'profile': profile_id,
                'path': 'downstream-01',
                'protocol': HardwareProfileRevision.Protocol.PCIE,
                'connector': 'MCIO x8',
                'lane_count': 8,
                'max_rate': '32 GT/s per lane',
                'supported_modes': ['PCIe 5.0'],
            },
            expected_code=201,
        )
        approved = self.post(
            reverse('cangxu-hardware-profile-approve', kwargs={'pk': profile_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(approved.data['state'], HardwareProfileRevision.State.APPROVED)
        self.assertEqual(approved.data['chip_vendor'], chip_vendor.pk)
        self.assertEqual(approved.data['board_manufacturer'], board_maker.pk)
        self.assertEqual(port.data['profile'], profile_id)
        self.patch(
            reverse('cangxu-hardware-profile-detail', kwargs={'pk': profile_id}),
            {'revision': 'R2'},
            expected_code=400,
        )

    def test_multibranch_power_harness_and_non_pcie_accelerator(self):
        """Allow harness breakouts and accelerator modules without PCIe assumptions."""
        part = Part.objects.get(pk=25)
        profile = self.post(
            reverse('cangxu-hardware-profile-list'),
            {
                'part': part.pk,
                'revision': 'A',
                'kind': HardwareProfileRevision.Kind.POWER_HARNESS,
                'protocol': HardwareProfileRevision.Protocol.GPU_POWER,
                'form_factor': HardwareProfileRevision.FormFactor.CABLE,
                'source_reference': 'Synthetic harness drawing DWG-CX-002',
            },
            expected_code=201,
        )
        for label in ['PSU-A', 'GPU-0A', 'GPU-0B']:
            self.post(
                reverse('cangxu-cable-end-list'),
                {
                    'profile': profile.data['id'],
                    'label': label,
                    'connector': 'High-current keyed connector',
                    'protocol': HardwareProfileRevision.Protocol.GPU_POWER,
                    'branch_group': 'GPU-0',
                    'lane_map': {'wire_count': 8, 'sense': 'synthetic'},
                },
                expected_code=201,
            )
        approved = self.post(
            reverse(
                'cangxu-hardware-profile-approve', kwargs={'pk': profile.data['id']}
            ),
            {},
            expected_code=200,
        )
        self.assertEqual(approved.data['state'], HardwareProfileRevision.State.APPROVED)

        accelerator = self.post(
            reverse('cangxu-hardware-profile-list'),
            {
                'part': Part.objects.get(pk=25).pk,
                'revision': 'B0',
                'kind': HardwareProfileRevision.Kind.GPU,
                'protocol': HardwareProfileRevision.Protocol.UNSPECIFIED,
                'form_factor': HardwareProfileRevision.FormFactor.MODULE,
                'source_reference': 'Synthetic accelerator module specification',
            },
            expected_code=201,
        )
        self.assertEqual(accelerator.data['form_factor'], 'module')

    def test_switch_protocol_mismatch_is_rejected(self):
        """Reject a switch profile whose primary protocol conflicts with its kind."""
        response = self.post(
            reverse('cangxu-hardware-profile-list'),
            {
                'part': Part.objects.get(pk=25).pk,
                'revision': 'R1',
                'kind': HardwareProfileRevision.Kind.ETHERNET_SWITCH,
                'protocol': HardwareProfileRevision.Protocol.PCIE,
                'source_reference': 'Synthetic source',
            },
            expected_code=400,
        )
        self.assertIn('protocol', response.data)

    def test_received_lot_links_to_native_purchase_order_line(self):
        """Trace a partial serialized receipt through the native PO workflow."""
        part = Part.objects.get(pk=25)
        supplier = Company.objects.create(
            name='Cangxu Receipt Test Supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='CX-TEST-RECEIPT-001'
        )
        order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-TEST-PO-RECEIPT-001'
        )
        line = PurchaseOrderLineItem.objects.create(
            order=order, part=supplier_part, quantity=2
        )
        order.place_order()
        location = StockLocation.objects.get(pk=7)
        batch_code = 'CX-TEST-LOT-RECEIPT-001'
        order.receive_line_item(
            line,
            location,
            2,
            self.user,
            status=StockStatus.QUARANTINED.value,
            batch_code=batch_code,
            serials=['CX-TEST-BOARD-0001', 'CX-TEST-BOARD-0002'],
        )

        response = self.post(
            reverse('cangxu-lot-list'),
            {'part': part.pk, 'code': batch_code, 'purchase_order_line': line.pk},
            expected_code=201,
        )
        self.assertEqual(response.data['purchase_order_line'], line.pk)
        lot_id = response.data['id']
        received_items = StockItem.objects.filter(
            purchase_order=order, batch=batch_code
        )
        self.assertEqual(received_items.count(), 2)
        for item in received_items:
            link_response = self.post(
                reverse('cangxu-lot-stock-item-list'),
                {'lot': lot_id, 'stock_item': item.pk},
                expected_code=201,
            )
            self.assertEqual(link_response.data['stock_item'], item.pk)

        wrong_part_response = self.post(
            reverse('cangxu-lot-list'),
            {
                'part': Part.objects.exclude(pk=part.pk).first().pk,
                'code': 'CX-TEST-LOT-WRONG-PART',
                'purchase_order_line': line.pk,
            },
            expected_code=400,
        )
        self.assertIn('purchase_order_line', wrong_part_response.data)


class CangxuConfigurationTest(CangxuAPITestCase):
    """Exercise atomic component installation and replacement."""

    def test_native_build_output_can_be_recorded_as_actual_configuration(self):
        """Bind a completed InvenTree Build output without installing parts twice."""
        location = StockLocation.objects.get(pk=7)
        assembly = Part.objects.create(
            name='Cangxu synthetic build output', assembly=True, trackable=True
        )
        component_part = Part.objects.create(
            name='Cangxu synthetic tracked component', component=True, trackable=True
        )
        BomItem.objects.create(part=assembly, sub_part=component_part, quantity=1)
        component = StockItem.objects.create(
            part=component_part,
            location=location,
            quantity=1,
            serial='CX-BUILD-COMP-0001',
            serial_int=1,
        )
        build = Build.objects.create(
            part=assembly,
            reference=generate_next_build_reference(),
            quantity=1,
            title='Synthetic native build workflow',
        )
        output = build.create_build_output(
            1, serials=['CX-BUILD-UNIT-0001'], user=self.user, location=location
        ).first()
        line = build.build_lines.get(bom_item__sub_part=component_part)

        response = self.post(
            reverse('api-build-allocate', kwargs={'pk': build.pk}),
            {
                'items': [
                    {
                        'build_line': line.pk,
                        'stock_item': component.pk,
                        'quantity': 1,
                        'output': output.pk,
                    }
                ]
            },
            expected_code=201,
        )
        self.assertEqual(response.status_code, 201)
        self.post(
            reverse('api-build-output-complete', kwargs={'pk': build.pk}),
            {
                'outputs': [{'output': output.pk}],
                'location': location.pk,
                'status': StockStatus.OK.value,
            },
            expected_code=200,
        )

        output.refresh_from_db()
        component.refresh_from_db()
        self.assertFalse(output.is_building)
        self.assertEqual(output.build_id, build.pk)
        self.assertEqual(component.belongs_to_id, output.pk)
        self.assertEqual(component.consumed_by_id, build.pk)

        config_response = self.post(
            reverse('cangxu-configuration-list'),
            {'unit': output.pk, 'change_summary': 'Synthetic build trace.'},
            expected_code=201,
        )
        item_response = self.post(
            reverse('cangxu-configuration-item-list'),
            {
                'configuration': config_response.data['id'],
                'component': component.pk,
                'position': 'CPU0',
                'quantity': 1,
            },
            expected_code=201,
        )
        self.assertEqual(item_response.data['component'], component.pk)
        self.assertEqual(item_response.data['source_build_line'], line.pk)
        component.refresh_from_db()
        self.assertEqual(component.belongs_to_id, output.pk)

        removal_response = self.post(
            reverse(
                'cangxu-configuration-item-remove',
                kwargs={'pk': item_response.data['id']},
            ),
            {
                'location': location.pk,
                'reason': 'Synthetic surplus component return',
                'removal_kind': ConfigurationItem.RemovalKind.SURPLUS_RETURN,
            },
            expected_code=200,
        )
        self.assertEqual(removal_response.data['source_build_line'], line.pk)
        self.assertEqual(
            removal_response.data['removal_kind'],
            ConfigurationItem.RemovalKind.SURPLUS_RETURN,
        )
        self.assertEqual(
            removal_response.data['removal_reason'],
            'Synthetic surplus component return',
        )
        component.refresh_from_db()
        self.assertIsNone(component.belongs_to_id)
        self.assertEqual(component.location_id, location.pk)
        self.assertEqual(
            component.tracking_info.order_by('-pk').first().notes,
            'surplus_return: Synthetic surplus component return',
        )
        self.post(
            reverse(
                'cangxu-configuration-item-remove',
                kwargs={'pk': item_response.data['id']},
            ),
            {
                'location': location.pk,
                'reason': 'Duplicate synthetic return',
                'removal_kind': ConfigurationItem.RemovalKind.SURPLUS_RETURN,
            },
            expected_code=400,
        )

    def test_component_replacement_preserves_stock_history(self):
        """Move the old component out and the replacement in as one operation."""
        unit = StockItem.objects.get(pk=1000)
        source = StockItem.objects.get(pk=100)
        replacement_source = StockItem.objects.get(pk=101)

        response = self.post(
            reverse('cangxu-configuration-list'),
            {'unit': unit.pk, 'kind': 'actual', 'change_summary': 'Test assembly'},
        )
        configuration_id = response.data['id']
        self.post(
            reverse('cangxu-configuration-item-list'),
            {
                'configuration': configuration_id,
                'component': source.pk,
                'position': 'GPU bay 01',
                'quantity': '2',
            },
        )

        installed = unit.installed_parts.get()
        configuration_item = unit.cangxu_configurations.get(
            pk=configuration_id
        ).items.get(removed_at__isnull=True)
        issue_response = self.post(
            reverse('cangxu-quality-issue-list'),
            {
                'reference': 'CX-REWORK-REPLACE-0001',
                'unit': unit.pk,
                'component': installed.pk,
                'title': 'Synthetic component failure',
                'severity': QualityIssue.Severity.HIGH,
            },
            expected_code=201,
        )
        task_response = self.post(
            reverse('cangxu-rework-task-list'),
            {
                'issue': issue_response.data['id'],
                'title': 'Synthetic component replacement',
            },
            expected_code=201,
        )
        replacement_url = reverse(
            'cangxu-configuration-item-replace', kwargs={'pk': configuration_item.pk}
        )
        replacement_data = {
            'replacement_item': replacement_source.pk,
            'destination_location': 7,
            'reason': 'Synthetic fixture replacement',
            'rework_task': task_response.data['id'],
        }
        self.post(replacement_url, replacement_data, expected_code=400)
        installed.refresh_from_db()
        replacement_source.refresh_from_db()
        self.assertEqual(installed.belongs_to_id, unit.pk)
        self.assertIsNone(replacement_source.belongs_to_id)
        self.post(
            reverse(
                'cangxu-quality-issue-transition',
                kwargs={'pk': issue_response.data['id']},
            ),
            {'state': QualityIssue.State.INVESTIGATING},
            expected_code=200,
        )
        self.post(
            reverse(
                'cangxu-quality-issue-transition',
                kwargs={'pk': issue_response.data['id']},
            ),
            {'state': QualityIssue.State.REWORK},
            expected_code=200,
        )
        self.post(
            reverse(
                'cangxu-rework-task-transition', kwargs={'pk': task_response.data['id']}
            ),
            {'state': ReworkTask.State.IN_PROGRESS},
            expected_code=200,
        )
        response = self.post(replacement_url, replacement_data, expected_code=200)

        self.assertEqual(response.status_code, 200)
        installed.refresh_from_db()
        replacement = StockItem.objects.get(pk=response.data['installed']['component'])
        replacement.refresh_from_db()
        self.assertIsNone(installed.belongs_to_id)
        self.assertEqual(installed.location_id, 7)
        self.assertEqual(replacement.belongs_to_id, unit.pk)
        self.assertEqual(
            unit.cangxu_replacements.get().replacement_item_id, replacement.pk
        )
        self.assertEqual(
            unit.cangxu_replacements.get().rework_task_id, task_response.data['id']
        )


class CangxuServiceCaseTest(CangxuAPITestCase):
    """Exercise supplier repair custody from send through inspection."""

    def test_customer_return_links_to_original_shipment(self):
        """Keep the shipped unit, customer, and return case on one traceable chain."""
        customer = Company.objects.create(
            name='Cangxu Return Test Customer', is_customer=True
        )
        unit_part = Part.objects.get(pk=StockItem.objects.get(pk=1000).part_id)
        unit = StockItem.objects.create(
            part=unit_part,
            location=StockLocation.objects.get(pk=7),
            quantity=1,
            serial='CX-RETURN-TEST-UNIT-0001',
            serial_int=1,
        )
        order = SalesOrder.objects.create(
            customer=customer, reference='CX-RETURN-TEST-SO-0001'
        )
        line = SalesOrderLineItem.objects.create(
            order=order, part=unit_part, quantity=1
        )
        shipment = SalesOrderShipment.objects.create(
            order=order, reference='CX-RETURN-TEST-SHIP-0001'
        )
        SalesOrderAllocation.objects.create(
            line=line, shipment=shipment, item=unit, quantity=1
        )
        pending_response = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-RETURN-TEST-CASE-PENDING',
                'kind': 'customer_return',
                'customer': customer.pk,
                'unit': unit.pk,
                'source_shipment': shipment.pk,
            },
            expected_code=400,
        )
        self.assertIn('source_shipment', pending_response.data)
        shipment.complete_allocations(shipment.allocations.all(), user=self.user)
        shipment.shipment_date = timezone.now().date()
        shipment.save(update_fields=['shipment_date'])

        response = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-RETURN-TEST-CASE-0001',
                'kind': 'customer_return',
                'customer': customer.pk,
                'unit': unit.pk,
                'source_shipment': shipment.pk,
                'description': 'Synthetic customer return linked to its shipment.',
            },
            expected_code=201,
        )
        case = ServiceCase.objects.get(pk=response.data['id'])
        self.assertEqual(case.source_shipment_id, shipment.pk)
        line_response = self.post(
            reverse('cangxu-service-line-list'),
            {'case': case.pk, 'stock_item': unit.pk, 'quantity': 1},
            expected_code=201,
        )
        receive_response = self.post(
            reverse('cangxu-service-event-list'),
            {
                'line': line_response.data['id'],
                'event_type': 'received',
                'company': customer.pk,
                'to_location': StockLocation.objects.get(pk=7).pk,
                'quantity': 1,
                'notes': 'Synthetic customer return receipt into quarantine.',
            },
            expected_code=201,
        )
        unit.refresh_from_db()
        self.assertEqual(unit.location_id, StockLocation.objects.get(pk=7).pk)
        self.assertEqual(unit.status, 75)
        self.assertIsNone(unit.customer_id)
        self.post(
            reverse('cangxu-service-event-list'),
            {
                'line': line_response.data['id'],
                'stock_item': unit.pk,
                'event_type': 'inspected',
                'inspection_passed': True,
                'quantity': 1,
            },
            expected_code=201,
        )
        self.post(
            reverse(
                'cangxu-service-line-resolve', kwargs={'pk': line_response.data['id']}
            ),
            {'outcome': 'no_fault', 'notes': 'Synthetic inspection passed.'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-service-case-close', kwargs={'pk': case.pk}),
            {},
            expected_code=200,
        )
        self.assertEqual(receive_response.data['event_type'], 'received')

        wrong_customer = Company.objects.create(
            name='Cangxu Mismatched Return Customer', is_customer=True
        )
        wrong_response = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-RETURN-TEST-CASE-0002',
                'kind': 'customer_return',
                'customer': wrong_customer.pk,
                'unit': unit.pk,
                'source_shipment': shipment.pk,
            },
            expected_code=400,
        )
        self.assertIn('source_shipment', wrong_response.data)

    def test_supplier_repair_moves_and_quarantines_stock(self):
        """Track vendor hand-offs and require inspection before closure."""
        component_part = Part.objects.get(pk=25)
        internal = StockLocation.objects.get(pk=7)
        external = StockLocation.objects.create(
            name='Cangxu external repair location', external=True
        )
        stock = StockItem.objects.create(
            part=component_part,
            location=internal,
            quantity=1,
            serial='CX-SVC-DEMO-0001',
            serial_int=0,
        )
        supplier = Company.objects.create(
            name='Cangxu Synthetic Supplier', is_supplier=True
        )

        response = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-SVC-DEMO-0001',
                'kind': 'supplier_repair',
                'supplier': supplier.pk,
                'description': 'Synthetic repair workflow',
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        case_id = response.data['id']
        response = self.post(
            reverse('cangxu-service-line-list'),
            {'case': case_id, 'stock_item': stock.pk, 'quantity': '1'},
        )
        line_id = response.data['id']
        event_url = reverse('cangxu-service-event-list')

        response = self.post(
            event_url,
            {
                'line': line_id,
                'event_type': 'sent',
                'company': supplier.pk,
                'to_location': external.pk,
                'notes': 'Synthetic outbound hand-off',
            },
        )
        self.assertEqual(response.status_code, 201)
        stock.refresh_from_db()
        self.assertEqual(stock.location_id, external.pk)

        response = self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': stock.pk,
                'event_type': 'external_received',
                'company': supplier.pk,
                'notes': 'Synthetic supplier receipt',
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        response = self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': stock.pk,
                'event_type': 'returned',
                'company': supplier.pk,
                'to_location': internal.pk,
                'notes': 'Synthetic return',
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        stock.refresh_from_db()
        self.assertEqual(stock.location_id, internal.pk)
        self.assertEqual(
            stock.status,
            75,
            list(
                stock.cangxu_service_events.values(
                    'event_type', 'stock_item_id', 'from_location_id', 'to_location_id'
                )
            ),
        )

        self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': stock.pk,
                'event_type': 'inspected',
                'inspection_passed': True,
                'notes': 'Synthetic inspection pass',
            },
        )
        self.post(
            reverse('cangxu-service-line-resolve', kwargs={'pk': line_id}),
            {'outcome': 'repaired', 'notes': 'Synthetic repair complete'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-service-case-close', kwargs={'pk': case_id}),
            {},
            expected_code=200,
        )
        stock.refresh_from_db()
        self.assertEqual(stock.status, 10)

    def test_replacement_can_be_installed_and_traced_to_service_case(self):
        """Link an inspected return, replacement stock, and its actual reinstallation."""
        unit = StockItem.objects.get(pk=1000)
        internal = StockLocation.objects.get(pk=7)
        external = StockLocation.objects.create(
            name='Cangxu replacement repair location', external=True
        )
        component_part = Part.objects.get(pk=25)
        original = StockItem.objects.create(
            part=component_part,
            location=internal,
            quantity=1,
            serial='CX-SVC-REPLACE-OLD-0001',
            serial_int=0,
        )
        replacement = StockItem.objects.create(
            part=component_part,
            location=internal,
            quantity=1,
            serial='CX-SVC-REPLACE-NEW-0001',
            serial_int=1,
        )
        unit.installStockItem(
            original, 1, self.user, 'Synthetic original component assembly'
        )
        original.refresh_from_db()
        original.uninstall_into_location(
            internal, self.user, 'Synthetic pre-repair removal'
        )
        supplier = Company.objects.create(
            name='Cangxu Replacement Supplier', is_supplier=True
        )
        case_response = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-SVC-REPLACE-0001',
                'kind': 'supplier_repair',
                'supplier': supplier.pk,
                'unit': unit.pk,
                'description': 'Synthetic replacement and reinstallation flow',
            },
        )
        case_id = case_response.data['id']
        line_response = self.post(
            reverse('cangxu-service-line-list'),
            {'case': case_id, 'stock_item': original.pk, 'quantity': '1'},
        )
        line_id = line_response.data['id']
        event_url = reverse('cangxu-service-event-list')
        self.post(
            event_url,
            {
                'line': line_id,
                'event_type': 'sent',
                'company': supplier.pk,
                'to_location': external.pk,
                'quantity': '1',
            },
            expected_code=201,
        )
        self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': original.pk,
                'event_type': 'external_received',
                'company': supplier.pk,
                'quantity': '1',
            },
            expected_code=201,
        )
        self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': original.pk,
                'event_type': 'returned',
                'company': supplier.pk,
                'to_location': internal.pk,
                'quantity': '1',
            },
            expected_code=201,
        )
        self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': original.pk,
                'event_type': 'inspected',
                'inspection_passed': True,
                'quantity': '1',
            },
            expected_code=201,
        )
        self.post(
            reverse('cangxu-service-line-resolve', kwargs={'pk': line_id}),
            {
                'outcome': 'replaced',
                'replacement_item': replacement.pk,
                'notes': 'Synthetic supplier replacement recorded.',
            },
            expected_code=200,
        )

        configuration_response = self.post(
            reverse('cangxu-configuration-list'),
            {
                'unit': unit.pk,
                'kind': 'actual',
                'change_summary': 'Synthetic replacement installed after inspection',
            },
        )
        self.assertEqual(configuration_response.status_code, 201)
        self.post(
            reverse('cangxu-configuration-item-list'),
            {
                'configuration': configuration_response.data['id'],
                'component': replacement.pk,
                'position': 'PCIE-SWITCH-01',
                'quantity': '1',
            },
            expected_code=201,
        )
        replacement.refresh_from_db()
        self.assertEqual(replacement.belongs_to_id, unit.pk)
        self.post(
            event_url,
            {
                'line': line_id,
                'stock_item': replacement.pk,
                'event_type': 'reinstalled',
                'quantity': '1',
                'notes': 'Synthetic new component installed into the original unit.',
            },
            expected_code=201,
        )
        self.post(
            reverse('cangxu-service-case-close', kwargs={'pk': case_id}),
            {},
            expected_code=200,
        )
        original.refresh_from_db()
        self.assertEqual(original.status, 10)
        self.assertEqual(
            original.cangxu_service_lines.get().replacement_item_id, replacement.pk
        )
        self.assertTrue(
            ServiceCaseEvent.objects.filter(
                line__case_id=case_id, event_type='reinstalled', stock_item=replacement
            ).exists()
        )


class CangxuQualityReworkTest(CangxuAPITestCase):
    """Require corrective work and a separate verification before closure."""

    def test_quality_issue_cannot_close_before_rework_verification(self):
        """Block closure until work and independent verification are recorded."""
        unit = StockItem.objects.get(pk=1000)
        response = self.post(
            reverse('cangxu-quality-issue-list'),
            {
                'reference': 'CX-QA-TEST-0001',
                'unit': unit.pk,
                'component': StockItem.objects.get(pk=100).pk,
                'title': 'Synthetic cooling-path verification',
                'severity': 'high',
                'description': 'Demonstration-only quality issue.',
            },
        )
        self.assertEqual(response.status_code, 201, response.data)
        issue_id = response.data['id']

        task_response = self.post(
            reverse('cangxu-rework-task-list'),
            {
                'issue': issue_id,
                'title': 'Repeat synthetic thermal test',
                'instructions': 'Use approved production instructions in real work.',
            },
        )
        self.assertEqual(task_response.status_code, 201, task_response.data)
        task_id = task_response.data['id']

        issue_close_url = reverse('cangxu-quality-issue-close', kwargs={'pk': issue_id})
        self.post(
            issue_close_url, {'verification_notes': 'Not ready'}, expected_code=400
        )
        self.post(
            reverse('cangxu-quality-issue-transition', kwargs={'pk': issue_id}),
            {'state': 'investigating'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-quality-issue-transition', kwargs={'pk': issue_id}),
            {'state': 'rework'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-rework-task-transition', kwargs={'pk': task_id}),
            {'state': 'in_progress'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-rework-task-transition', kwargs={'pk': task_id}),
            {'state': 'verify', 'note': 'Synthetic corrective action completed.'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-rework-task-verify', kwargs={'pk': task_id}),
            {'note': 'Independent synthetic verification passed.'},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-quality-issue-transition', kwargs={'pk': issue_id}),
            {'state': 'verify'},
            expected_code=200,
        )
        close_response = self.post(
            issue_close_url,
            {'verification_notes': 'Synthetic verification evidence recorded.'},
            expected_code=200,
        )
        self.assertEqual(close_response.data['state'], 'closed')


class CangxuCountSessionTest(CangxuAPITestCase):
    """Exercise the physical count, review, and close workflow."""

    def test_count_requires_every_line_to_be_counted_and_reviewed(self):
        """Only an independently reviewed count can close against core stock."""
        location = StockLocation.objects.get(pk=7)
        response = self.post(
            reverse('cangxu-count-session-list'),
            {'reference': 'CX-COUNT-TEST-0001', 'location': location.pk},
        )
        session = CountSession.objects.get(pk=response.data['id'])
        lines = list(session.lines.select_related('stock_item'))
        self.assertTrue(lines)

        submit_url = reverse('cangxu-count-session-submit', kwargs={'pk': session.pk})
        self.post(submit_url, {}, expected_code=400)

        for line in lines:
            self.patch(
                reverse('cangxu-count-line-detail', kwargs={'pk': line.pk}),
                {'counted_quantity': str(line.expected_quantity)},
                expected_code=200,
            )

        self.post(submit_url, {}, expected_code=200)
        for line in lines:
            self.post(
                reverse('cangxu-count-line-review', kwargs={'pk': line.pk}),
                {},
                expected_code=200,
            )

        with self.captureOnCommitCallbacks(execute=True):
            self.post(
                reverse('cangxu-count-session-close', kwargs={'pk': session.pk}),
                {},
                expected_code=200,
            )
        session.refresh_from_db()
        self.assertEqual(session.state, CountSession.State.CLOSED)
        stock_count_notes = f'Cangxu count {session.reference}:'
        self.assertEqual(
            StockItemTracking.objects.filter(
                item__in=[line.stock_item for line in lines],
                tracking_type=StockHistoryCode.STOCK_COUNT,
                notes__startswith=stock_count_notes,
            ).count(),
            len(lines),
        )


class CangxuShipmentManifestTest(CangxuAPITestCase):
    """Exercise package verification across separate shipments of one order."""

    def test_split_shipments_freeze_only_their_allocated_items(self):
        """Manifest snapshots follow each shipment allocation without shipping stock."""
        customer = Company.objects.create(
            name='Cangxu Synthetic Customer', is_customer=True
        )
        unit_part = Part.objects.get(pk=StockItem.objects.get(pk=1000).part_id)
        order = SalesOrder.objects.create(
            customer=customer,
            reference='CX-SHIP-TEST-0001',
            description='Synthetic split-shipment API test',
        )
        line = SalesOrderLineItem.objects.create(
            order=order, part=unit_part, quantity=2
        )
        units = [
            StockItem.objects.create(
                part=unit_part,
                location=StockLocation.objects.get(pk=7),
                quantity=1,
                serial=f'CX-SHIP-TEST-{index:04d}',
                serial_int=index,
            )
            for index in (1, 2)
        ]
        shipments = []
        manifests = []
        component_source = StockItem.objects.get(pk=100)
        units[0].installStockItem(
            component_source, 1, self.user, 'Synthetic split-shipment API test assembly'
        )
        configured_component = units[0].installed_parts.get()
        released_configuration = UnitConfiguration.objects.create(
            unit=units[0],
            revision=1,
            kind=UnitConfiguration.Kind.ACTUAL,
            state=UnitConfiguration.State.RELEASED,
        )
        ConfigurationItem.objects.create(
            configuration=released_configuration,
            component=configured_component,
            position='GPU bay 01',
            quantity=1,
        )
        for index, unit in enumerate(units, 1):
            shipment = SalesOrderShipment.objects.create(
                order=order, reference=f'CX-SHIP-TEST-{index:04d}'
            )
            SalesOrderAllocation.objects.create(
                line=line, shipment=shipment, item=unit, quantity=1
            )
            manifest = ShipmentManifest.objects.create(
                shipment=shipment,
                package_code=f'CX-PKG-TEST-{index:04d}',
                configuration=(released_configuration if index == 1 else None),
            )
            self.post(
                reverse('cangxu-manifest-line-list'),
                {'manifest': manifest.pk, 'stock_item': unit.pk, 'item_role': 'server'},
            )
            shipments.append(shipment)
            manifests.append(manifest)

        # The first package cannot claim the unit allocated to the second shipment.
        response = self.post(
            reverse('cangxu-manifest-line-list'),
            {
                'manifest': manifests[0].pk,
                'stock_item': units[1].pk,
                'item_role': 'wrong package',
            },
        )
        self.assertEqual(response.status_code, 201)
        response = self.post(
            reverse('cangxu-manifest-verify', kwargs={'pk': manifests[0].pk}),
            {},
            expected_code=400,
        )
        self.assertEqual(response.status_code, 400)
        # Remove the deliberately incorrect scan; then both shipment manifests
        # can be checked for their remaining package rules.
        wrong_line = manifests[0].lines.get(stock_item=units[1])
        wrong_line.delete()
        response = self.post(
            reverse('cangxu-manifest-verify', kwargs={'pk': manifests[0].pk}),
            {},
            expected_code=400,
        )
        self.assertIn('missing', str(response.data).lower())
        self.post(
            reverse('cangxu-manifest-line-list'),
            {
                'manifest': manifests[0].pk,
                'stock_item': configured_component.pk,
                'item_role': 'configured component',
            },
            expected_code=201,
        )
        for manifest, unit, shipment in zip(manifests, units, shipments, strict=True):
            response = self.post(
                reverse('cangxu-manifest-verify', kwargs={'pk': manifest.pk}),
                {},
                expected_code=200,
            )
            self.assertEqual(response.status_code, 200)
            self.assertEqual(len(response.data['content_hash']), 64)
            self.assertEqual(
                {
                    row['stock_item']
                    for row in response.data['contents_snapshot']['lines']
                },
                ({unit.pk, configured_component.pk} if unit == units[0] else {unit.pk}),
            )
            shipment.refresh_from_db()
            self.assertIsNone(shipment.shipment_date)
        self.assertEqual(order.lines.get().shipped, 0)


class CangxuDemoSeedTest(CangxuAPITestCase):
    """Check deterministic demo expansion and rerun behavior."""

    def test_demo_seed_scales_up_idempotently(self):
        """A larger factor adds synthetic records; repeating it adds none."""
        call_command('seed_cangxu_demo', scale_factor=1)
        hardware_profiles = HardwareProfileRevision.objects.filter(
            part__IPN__startswith='CX-DEMO-'
        )
        self.assertEqual(hardware_profiles.count(), 17)
        self.assertTrue(
            hardware_profiles.filter(state=HardwareProfileRevision.State.DRAFT).exists()
        )
        self.assertFalse(
            hardware_profiles.filter(
                state=HardwareProfileRevision.State.APPROVED
            ).exists()
        )
        linkreal_profile = hardware_profiles.get(part__IPN='CX-DEMO-PCIESW-LR-001')
        self.assertIn('联瑞', linkreal_profile.board_manufacturer.name)
        self.assertIn('其他类别', linkreal_profile.chip_vendor.name)
        self.assertEqual(
            linkreal_profile.kind, HardwareProfileRevision.Kind.PCIE_SWITCH
        )
        ethernet_profile = hardware_profiles.get(part__IPN='CX-DEMO-ETHSW-001')
        infiniband_profile = hardware_profiles.get(part__IPN='CX-DEMO-IBSW-001')
        self.assertEqual(
            ethernet_profile.kind, HardwareProfileRevision.Kind.ETHERNET_SWITCH
        )
        self.assertEqual(
            infiniband_profile.kind, HardwareProfileRevision.Kind.INFINIBAND_SWITCH
        )
        branch_profile = hardware_profiles.get(part__IPN='CX-DEMO-BRANCH-001')
        self.assertEqual(branch_profile.cable_ends.count(), 3)
        self.assertFalse(linkreal_profile.cable_ends.exists())
        self.assertTrue(
            CableEndDefinition.objects.filter(profile=branch_profile).exists()
        )
        initial_stock = StockItem.objects.filter(
            part__IPN__startswith='CX-DEMO-'
        ).count()
        initial_configurations = UnitConfiguration.objects.filter(
            unit__part__IPN__startswith='CX-DEMO-'
        ).count()
        initial_service_cases = ServiceCase.objects.filter(
            reference__startswith='CX-DEMO-RMA-'
        ).count()

        call_command('seed_cangxu_demo', scale_factor=2)
        expanded_stock = StockItem.objects.filter(
            part__IPN__startswith='CX-DEMO-'
        ).count()
        expanded_configurations = UnitConfiguration.objects.filter(
            unit__part__IPN__startswith='CX-DEMO-'
        ).count()
        expanded_service_cases = ServiceCase.objects.filter(
            reference__startswith='CX-DEMO-RMA-'
        ).count()

        self.assertGreater(expanded_stock, initial_stock)
        self.assertGreater(expanded_configurations, initial_configurations)
        self.assertGreater(expanded_service_cases, initial_service_cases)
        self.assertEqual(
            HardwareProfileRevision.objects.filter(
                part__IPN__startswith='CX-DEMO-'
            ).count(),
            17,
        )
        self.assertEqual(expanded_service_cases, 32)
        self.assertEqual(
            PurchaseOrderLineItem.objects.get(
                order__reference='CX-DEMO-PO-0001'
            ).received,
            4,
        )
        self.assertEqual(
            PurchaseOrderLineItem.objects.get(
                order__reference='CX-DEMO-PO-0002'
            ).received,
            24,
        )

        call_command('seed_cangxu_demo', scale_factor=2)
        self.assertEqual(
            StockItem.objects.filter(part__IPN__startswith='CX-DEMO-').count(),
            expanded_stock,
        )
        self.assertEqual(
            UnitConfiguration.objects.filter(
                unit__part__IPN__startswith='CX-DEMO-'
            ).count(),
            expanded_configurations,
        )
        self.assertEqual(
            ServiceCase.objects.filter(reference__startswith='CX-DEMO-RMA-').count(),
            expanded_service_cases,
        )


class CangxuDataImportTestCase(CangxuAPITestCase):
    """Exercise staged inventory imports without bypassing review or traceability."""

    def create_opening_batch(self, digest):
        """Create a fictional, physically verified opening-balance batch."""
        return self.post(
            reverse('cangxu-import-batch-list'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.OPENING_STOCK,
                'source_file_name': 'synthetic-opening-stock.xlsx',
                'source_file_digest': digest,
                'inventory_as_of': '2026-10-01',
                'physical_count_confirmed': True,
            },
            expected_code=201,
        )

    def test_xlsx_upload_stages_cell_provenance_idempotently(self):
        """Parse a fictional workbook while preserving leading zeros and coordinates."""
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Synthetic inventory'
        sheet.append(['PN号', '数量', 'SN号', '生产日期', '本年度生产批次'])
        sheet.append(['00001234', 3, 'SN0001-SN0004', '5.25', 'CX-TEST-LOT-001'])
        sheet['B2'].number_format = '0.000'
        sheet.append([1234, 1, 'SN0005', '2026-10-01', 'CX-TEST-LOT-002'])
        sheet['A3'].number_format = '000000'
        sheet.append([9876, 1, 'SN0006', '2026-10-02', 'CX-TEST-LOT-003'])
        shipment = workbook.create_sheet('Synthetic shipment')
        shipment.append([
            '流程编号',
            '项目名称',
            '出库产品',
            '数量',
            '状态',
            '出库时间',
        ])
        shipment.append([
            'CX-TEST-FLOW-0001',
            'Synthetic project',
            'Synthetic GPU board',
            2,
            '未出库',
            '2026-10-01',
        ])
        service = workbook.create_sheet('Synthetic service')
        service.append([
            '料号',
            '名称',
            '数量',
            'SN',
            '故障原因具体描述',
            '售后状态',
            '售后出库',
            '售后入库',
        ])
        service.append([
            'CX-TEST-PART-001',
            'Synthetic switch board',
            1,
            'CX-TEST-SN-0001',
            'Synthetic inspection required',
            '待检',
            None,
            None,
        ])
        detail = workbook.create_sheet('Synthetic trace')
        detail['B4'] = 'CX-TEST-SN-0002'
        content = BytesIO()
        workbook.save(content)
        stock_count = StockItem.objects.count()

        def upload_workbook():
            return SimpleUploadedFile(
                'synthetic.xlsx',
                content.getvalue(),
                content_type=(
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
            )

        response = self.post(
            reverse('cangxu-import-batch-upload'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.PURCHASE_HISTORY,
                'source_file': upload_workbook(),
            },
            expected_code=201,
            format='multipart',
        )
        self.assertEqual(response.data['worksheet_rows'], 9)
        self.assertEqual(response.data['data_rows'], 6)
        self.assertEqual(response.data['staged_rows'], 6)
        batch_id = response.data['batch']['id']
        first_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic inventory', source_row=2
        )
        self.assertEqual(first_row.source_range, 'A2:E2')
        self.assertEqual(first_row.source_values['A']['value'], '00001234')
        self.assertEqual(first_row.source_values['B']['number_format'], '0.000')
        self.assertEqual(first_row.normalized_values['source_headers']['source_row'], 1)
        self.assertEqual(
            first_row.normalized_values['source_headers']['source_values']['A'][
                'value'
            ],
            'PN号',
        )
        self.assertEqual(
            first_row.normalized_values['fields'],
            {
                'part_number': '00001234',
                'quantity': 3,
                'serial': 'SN0001-SN0004',
                'production_date': '5.25',
                'batch_code': 'CX-TEST-LOT-001',
            },
        )
        numeric_identifier_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic inventory', source_row=3
        )
        self.assertEqual(
            numeric_identifier_row.normalized_values['fields']['part_number'], '001234'
        )
        unformatted_identifier_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic inventory', source_row=4
        )
        self.assertEqual(
            unformatted_identifier_row.normalized_values['identifier_warnings'][0][
                'code'
            ],
            'identifier_stored_as_number',
        )
        shipment_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic shipment', source_row=2
        )
        self.assertEqual(
            shipment_row.normalized_values['mapping_profile'], 'shipment_history'
        )
        self.assertEqual(
            shipment_row.normalized_values['fields']['external_reference'],
            'CX-TEST-FLOW-0001',
        )
        service_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic service', source_row=2
        )
        self.assertEqual(
            service_row.normalized_values['mapping_profile'], 'service_history'
        )
        self.assertEqual(
            service_row.normalized_values['fields']['fault_description'],
            'Synthetic inspection required',
        )
        detail_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic trace', source_row=4
        )
        self.assertEqual(detail_row.source_range, 'B4:B4')

        repeated = self.post(
            reverse('cangxu-import-batch-upload'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.PURCHASE_HISTORY,
                'source_file': upload_workbook(),
            },
            expected_code=200,
            format='multipart',
        )
        self.assertEqual(repeated.data['batch']['id'], batch_id)
        self.assertEqual(repeated.data['staged_rows'], 0)
        self.assertEqual(repeated.data['already_staged_rows'], 6)
        validation = self.post(
            reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(validation.data['invalid'], 6)
        first_row.refresh_from_db()
        error_codes = {error['code'] for error in first_row.validation_errors}
        self.assertIn('date_missing_year', error_codes)
        self.assertIn('serial_range_quantity_mismatch', error_codes)
        unformatted_identifier_row.refresh_from_db()
        self.assertIn(
            'identifier_stored_as_number',
            {error['code'] for error in unformatted_identifier_row.validation_errors},
        )
        self.assertFalse(
            DataImportRecord.objects.filter(
                batch_id=batch_id, state=DataImportRecord.State.VALID
            ).exists()
        )
        self.assertEqual(StockItem.objects.count(), stock_count)

    def test_opening_import_requires_review_and_applies_idempotently(self):
        """Preserve source cells, then write one native stock item after approval."""
        part = Part.objects.create(
            name='Synthetic imported tracked part', trackable=True, component=True
        )
        PartCodeAlias.objects.create(
            part=part,
            namespace=PartCodeAlias.Namespace.LEGACY,
            code='0001002',
            source_system='CX-TEST',
        )
        location = StockLocation.objects.get(pk=7)
        batch_response = self.create_opening_batch('a' * 64)
        batch_id = batch_response.data['id']
        row_response = self.post(
            reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
            [
                {
                    'source_sheet': 'Synthetic stock',
                    'source_row': 2,
                    'source_range': 'A2:F2',
                    'source_values': {'legacy_code': '0001002', 'quantity': '1'},
                    'normalized_values': {
                        'fields': {
                            'part_number': '0001002',
                            'quantity': '1',
                            'serial': 'CX-TEST-IMPORT-0001',
                            'batch_code': 'CX-TEST-OPENING-001',
                        }
                    },
                }
            ],
            expected_code=201,
        )
        self.assertEqual(row_response.data['created'], 1)
        repeated_rows = self.post(
            reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
            [
                {
                    'source_sheet': 'Synthetic stock',
                    'source_row': 2,
                    'source_range': 'A2:F2',
                    'source_values': {'legacy_code': '0001002', 'quantity': '1'},
                    'normalized_values': {
                        'fields': {
                            'part_number': '0001002',
                            'quantity': '1',
                            'serial': 'CX-TEST-IMPORT-0001',
                            'batch_code': 'CX-TEST-OPENING-001',
                        }
                    },
                }
            ],
            expected_code=201,
        )
        self.assertEqual(repeated_rows.data['created'], 0)
        self.assertEqual(repeated_rows.data['already_staged'], 1)
        record = DataImportRecord.objects.get(batch_id=batch_id)
        mapped = self.post(
            reverse('cangxu-import-batch-map-opening-stock', kwargs={'pk': batch_id}),
            {'location': location.pk},
            expected_code=200,
        )
        self.assertEqual(mapped.data['mapped'], 1)
        record.refresh_from_db()
        self.assertEqual(record.mapped_part_id, part.pk)
        self.assertEqual(record.location_id, location.pk)
        self.assertEqual(record.quantity, 1)
        self.assertEqual(record.serial, 'CX-TEST-IMPORT-0001')
        self.assertEqual(record.batch_code, 'CX-TEST-OPENING-001')

        before_count = StockItem.objects.filter(part=part).count()
        self.post(
            reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(StockItem.objects.filter(part=part).count(), before_count)
        record.refresh_from_db()
        self.assertEqual(record.state, DataImportRecord.State.VALID)
        self.assertEqual(record.source_values['legacy_code'], '0001002')

        self.post(
            reverse('cangxu-import-batch-approve', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        applied = self.post(
            reverse('cangxu-import-batch-apply', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(applied.data['applied'], 1)
        self.assertEqual(StockItem.objects.filter(part=part).count(), 1)
        self.assertEqual(
            ManufacturingLotStockItem.objects.filter(stock_item__part=part).count(), 1
        )

        repeated = self.post(
            reverse('cangxu-import-batch-apply', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertTrue(repeated.data['already_applied'])
        self.assertEqual(StockItem.objects.filter(part=part).count(), 1)

        duplicate = self.post(
            reverse('cangxu-import-batch-list'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.OPENING_STOCK,
                'source_file_name': 'renamed-copy.xlsx',
                'source_file_digest': 'A' * 64,
                'inventory_as_of': '2026-10-01',
                'physical_count_confirmed': True,
            },
            expected_code=200,
        )
        self.assertEqual(duplicate.data['id'], batch_id)

    def test_opening_mapping_holds_part_code_ambiguity(self):
        """Do not select a part when the same external code has multiple targets."""
        first_part = Part.objects.create(
            name='Synthetic ambiguous part one', component=True
        )
        second_part = Part.objects.create(
            name='Synthetic ambiguous part two', component=True
        )
        for part, namespace in [
            (first_part, PartCodeAlias.Namespace.LEGACY),
            (second_part, PartCodeAlias.Namespace.ERP),
        ]:
            PartCodeAlias.objects.create(
                part=part,
                namespace=namespace,
                code='CX-TEST-AMBIGUOUS-001',
                source_system='CX-TEST',
            )
        batch_id = self.create_opening_batch('d' * 64).data['id']
        self.post(
            reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
            [
                {
                    'source_sheet': 'Synthetic stock',
                    'source_row': 2,
                    'source_values': {'part_number': 'CX-TEST-AMBIGUOUS-001'},
                    'normalized_values': {
                        'fields': {
                            'part_number': 'CX-TEST-AMBIGUOUS-001',
                            'quantity': 1,
                            'serial': 'CX-TEST-AMBIGUOUS-SN-001',
                            'batch_code': 'CX-TEST-AMBIGUOUS-BATCH',
                        }
                    },
                }
            ],
            expected_code=201,
        )

        response = self.post(
            reverse('cangxu-import-batch-map-opening-stock', kwargs={'pk': batch_id}),
            {'location': StockLocation.objects.get(pk=7).pk},
            expected_code=200,
        )
        self.assertEqual(response.data['mapped'], 0)
        self.assertEqual(response.data['unresolved'], 1)
        record = DataImportRecord.objects.get(batch_id=batch_id)
        self.assertIsNone(record.mapped_part_id)
        self.assertIn(
            'ambiguous_part_code', [error['code'] for error in record.validation_errors]
        )

    def test_invalid_serialized_quantity_cannot_be_approved_or_applied(self):
        """Hold serial/quantity conflicts in review without touching inventory."""
        part = Part.objects.create(
            name='Synthetic invalid imported tracked part',
            trackable=True,
            component=True,
        )
        location = StockLocation.objects.get(pk=7)
        batch_id = self.create_opening_batch('b' * 64).data['id']
        self.post(
            reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
            [
                {
                    'source_sheet': 'Synthetic stock',
                    'source_row': 3,
                    'source_values': {'legacy_code': '0001003', 'quantity': '2'},
                }
            ],
            expected_code=201,
        )
        record = DataImportRecord.objects.get(batch_id=batch_id)
        record.mapped_part = part
        record.location = location
        record.quantity = 2
        record.serial = 'CX-TEST-IMPORT-0002'
        record.batch_code = 'CX-TEST-OPENING-002'
        record.save()

        self.post(
            reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        record.refresh_from_db()
        self.assertEqual(record.state, DataImportRecord.State.INVALID)
        self.assertIn(
            'serialized_quantity_must_be_one',
            [error['code'] for error in record.validation_errors],
        )
        before_count = StockItem.objects.filter(part=part).count()
        self.post(
            reverse('cangxu-import-batch-approve', kwargs={'pk': batch_id}),
            {},
            expected_code=400,
        )
        self.assertEqual(StockItem.objects.filter(part=part).count(), before_count)
        rejected = self.post(
            reverse('cangxu-import-batch-reject', kwargs={'pk': batch_id}),
            {'note': 'Synthetic test rejection.'},
            expected_code=200,
        )
        self.assertEqual(rejected.data['state'], DataImportBatch.State.REJECTED)
        record.refresh_from_db()
        self.assertEqual(record.state, DataImportRecord.State.REJECTED)
