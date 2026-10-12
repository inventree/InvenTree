"""Integration tests for Cangxu inventory workflows."""

from datetime import date
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
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    MaterialIssue,
    MaterialReturn,
    PartCodeAlias,
    PurchaseReceipt,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseEvent,
    ShipmentManifest,
    ShipmentManifestLine,
    ShipmentReceipt,
    ShipmentReceiptException,
    ShipmentReceiptLine,
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


class CangxuPurchaseReceiptTest(CangxuAPITestCase):
    """Verify safe retries and lot traceability for native purchase receipts."""

    def test_bulk_receipts_are_atomic_and_idempotent(self):
        """Post two selected lines together and replay without duplicate stock."""
        part = Part.objects.filter(
            trackable=False, virtual=False, assembly=False
        ).first()
        self.assertIsNotNone(part)
        supplier = Company.objects.create(
            name='Cangxu Bulk Receipt Supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='CX-BULK-RECEIPT-001'
        )
        order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-BULK-RECEIPT-PO-001'
        )
        lines = [
            PurchaseOrderLineItem.objects.create(
                order=order, part=supplier_part, quantity=1
            )
            for _ in range(2)
        ]
        order.place_order()
        location = StockLocation.objects.get(pk=7)
        payload = {
            'receipts': [
                {
                    'idempotency_key': key,
                    'purchase_order_line': line.pk,
                    'quantity': '1',
                    'location': location.pk,
                    'packaging': f'synthetic tray {index}',
                }
                for index, (line, key) in enumerate(
                    zip(
                        lines,
                        [
                            '284e9172-cdc7-4cbc-92e4-4d5dd5dc9da1',
                            'c30a4145-3840-4b94-84a0-b212f5067fca',
                        ],
                        strict=True,
                    ),
                    start=1,
                )
            ]
        }
        url = reverse('cangxu-purchase-receipt-list')

        first = self.post(url, payload, expected_code=201)
        replay = self.post(url, payload, expected_code=200)

        self.assertEqual(
            [row['id'] for row in replay.data], [row['id'] for row in first.data]
        )
        self.assertEqual(
            [row['stock_items'] for row in replay.data],
            [row['stock_items'] for row in first.data],
        )
        self.assertEqual(
            PurchaseReceipt.objects.filter(purchase_order_line__order=order).count(), 2
        )
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 2)
        for line in lines:
            line.refresh_from_db()
            self.assertEqual(line.received, 1)

    def test_bulk_receipt_failure_rolls_back_earlier_lines(self):
        """Reject an over-receipt without leaving earlier bulk rows posted."""
        part = Part.objects.filter(
            trackable=False, virtual=False, assembly=False
        ).first()
        self.assertIsNotNone(part)
        supplier = Company.objects.create(
            name='Cangxu Bulk Rollback Supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='CX-BULK-ROLLBACK-001'
        )
        order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-BULK-ROLLBACK-PO-001'
        )
        lines = [
            PurchaseOrderLineItem.objects.create(
                order=order, part=supplier_part, quantity=1
            )
            for _ in range(2)
        ]
        order.place_order()
        location = StockLocation.objects.get(pk=7)
        payload = {
            'receipts': [
                {
                    'idempotency_key': key,
                    'purchase_order_line': line.pk,
                    'quantity': quantity,
                    'location': location.pk,
                }
                for line, key, quantity in zip(
                    lines,
                    [
                        'd0440752-5890-43e3-aefd-e7c28500713f',
                        'da467b38-9ce3-4650-a210-274b2b1b3486',
                    ],
                    ['1', '2'],
                    strict=True,
                )
            ]
        }

        self.post(reverse('cangxu-purchase-receipt-list'), payload, expected_code=400)

        self.assertEqual(
            PurchaseReceipt.objects.filter(purchase_order_line__order=order).count(), 0
        )
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 0)
        for line in lines:
            line.refresh_from_db()
            self.assertEqual(line.received, 0)

    def test_nonserialized_receipt_preserves_packaging_and_barcode_on_retry(self):
        """Retain native receiving metadata when posting through the retry-safe API."""
        part = Part.objects.filter(
            trackable=False, virtual=False, assembly=False
        ).first()
        self.assertIsNotNone(part)
        supplier = Company.objects.create(
            name='Cangxu Packaging Receipt Supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='CX-PACKAGING-RECEIPT-001'
        )
        order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-PACKAGING-RECEIPT-PO-001'
        )
        line = PurchaseOrderLineItem.objects.create(
            order=order, part=supplier_part, quantity=1
        )
        order.place_order()
        payload = {
            'idempotency_key': '9d936909-653a-4591-9c3a-9f54afed7c7c',
            'purchase_order_line': line.pk,
            'quantity': '1',
            'location': StockLocation.objects.get(pk=7).pk,
            'status': StockStatus.QUARANTINED.value,
            'packaging': 'synthetic foam tray',
            'barcode': 'CX-PACKAGING-BARCODE-001',
        }
        url = reverse('cangxu-purchase-receipt-list')

        first = self.post(url, payload, expected_code=201)
        replay = self.post(url, payload, expected_code=200)

        self.assertEqual(replay.data['id'], first.data['id'])
        self.assertEqual(replay.data['stock_items'], first.data['stock_items'])
        receipt = PurchaseReceipt.objects.get(pk=first.data['id'])
        self.assertEqual(receipt.packaging, payload['packaging'])
        self.assertEqual(receipt.barcode, payload['barcode'])
        item = StockItem.objects.get(pk=first.data['stock_items'][0])
        self.assertEqual(item.packaging, payload['packaging'])
        self.assertEqual(item.barcode_data, payload['barcode'])
        line.refresh_from_db()
        self.assertEqual(line.received, 1)
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 1)

    def test_split_serialized_receipts_are_idempotent_and_link_to_one_lot(self):
        """Receive one PO line in two calls and make a retry return the same stock."""
        part = Part.objects.get(pk=25)
        supplier = Company.objects.create(
            name='Cangxu Idempotent Receipt Supplier', is_supplier=True
        )
        supplier_part = SupplierPart.objects.create(
            part=part, supplier=supplier, SKU='CX-IDEMPOTENT-RECEIPT-001'
        )
        order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-IDEMPOTENT-PO-001'
        )
        line = PurchaseOrderLineItem.objects.create(
            order=order, part=supplier_part, quantity=2
        )
        order.place_order()
        location = StockLocation.objects.get(pk=7)
        url = reverse('cangxu-purchase-receipt-list')
        first_payload = {
            'idempotency_key': '54010c2c-1cf2-4400-92e2-66c0a2fc1942',
            'purchase_order_line': line.pk,
            'quantity': '1',
            'location': location.pk,
            'status': StockStatus.QUARANTINED.value,
            'batch_code': 'CX-IDEMPOTENT-LOT-001',
            'serial_numbers': ['CX-IDEMPOTENT-SN-0001'],
            'note': 'Synthetic first split receipt.',
        }

        first = self.post(url, first_payload, expected_code=201)
        replay = self.post(url, first_payload, expected_code=200)
        self.assertEqual(replay.data['id'], first.data['id'])
        self.assertEqual(replay.data['stock_items'], first.data['stock_items'])
        self.assertEqual(len(first.data['stock_items']), 1)
        line.refresh_from_db()
        self.assertEqual(line.received, 1)
        self.assertEqual(
            PurchaseReceipt.objects.filter(purchase_order_line=line).count(), 1
        )
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 1)

        conflicting_replay = {**first_payload, 'note': 'Changed after timeout.'}
        self.post(url, conflicting_replay, expected_code=400)
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 1)

        second_payload = {
            **first_payload,
            'idempotency_key': '8c02c9d4-e238-486a-8ca9-125c8d571953',
            # The warehouse form submits the native serial entry string; the
            # API expands it using InvenTree's serial-number rules.
            'serial_numbers': 'CX-IDEMPOTENT-SN-0002',
            'note': 'Synthetic second split receipt.',
        }
        second = self.post(url, second_payload, expected_code=201)
        line.refresh_from_db()
        lot = ManufacturingLot.objects.get(part=part, code=first_payload['batch_code'])
        self.assertEqual(line.received, 2)
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 2)
        self.assertEqual(lot.stock_items.count(), 2)
        self.assertEqual(len(second.data['stock_items']), 1)
        excess_payload = {
            **second_payload,
            'idempotency_key': '972952af-e31a-4e98-932a-eccf81f2a7ce',
            'serial_numbers': ['CX-IDEMPOTENT-SN-0003'],
        }
        self.post(url, excess_payload, expected_code=400)
        self.assertEqual(StockItem.objects.filter(purchase_order=order).count(), 2)


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


class CangxuMaterialIssueTest(CangxuAPITestCase):
    """Exercise consumable issue, partial return, and idempotent replay."""

    def test_issue_and_return_consumable_against_native_stock_and_build_line(self):
        """Keep stock, line consumption, tracking, and request replay consistent."""
        location = StockLocation.objects.get(pk=7)
        assembly = Part.objects.get(pk=25)
        material = Part.objects.get(pk=1)
        bom = BomItem.objects.create(
            part=assembly, sub_part=material, quantity=3, consumable=True
        )
        build = Build.objects.create(
            part=assembly,
            reference=generate_next_build_reference(),
            quantity=2,
            title='Synthetic consumable issue build',
        )
        line = build.build_lines.get(bom_item=bom)
        stock = StockItem.objects.create(part=material, location=location, quantity=10)
        issue_key = 'be5fa511-f1c8-4bb8-a440-74240f914501'
        issue_url = reverse('cangxu-material-issue-list')
        issue_data = {
            'build_line': line.pk,
            'stock_item': stock.pk,
            'quantity': '3',
            'idempotency_key': issue_key,
            'notes': 'Synthetic consumable issue.',
        }

        issue = self.post(issue_url, issue_data, expected_code=201)
        self.assertEqual(issue.data['quantity'], '3.00000')
        issued_stock = StockItem.objects.get(pk=issue.data['consumed_stock_item'])
        stock.refresh_from_db()
        line.refresh_from_db()
        self.assertEqual(stock.quantity, 7)
        self.assertEqual(issued_stock.quantity, 3)
        self.assertEqual(issued_stock.consumed_by_id, build.pk)
        self.assertEqual(line.consumed, 3)
        self.assertTrue(
            StockItemTracking.objects.filter(
                item=issued_stock, tracking_type=StockHistoryCode.BUILD_CONSUMED
            ).exists()
        )

        replay = self.post(issue_url, issue_data, expected_code=200)
        self.assertEqual(replay.data['id'], issue.data['id'])
        self.assertEqual(MaterialIssue.objects.filter(build_line=line).count(), 1)
        stock.refresh_from_db()
        self.assertEqual(stock.quantity, 7)

        return_data = {
            'quantity': '1',
            'location': location.pk,
            'idempotency_key': '4d5346c1-3026-4f7b-88ec-d6b24f4f4b76',
            'notes': 'Synthetic unused material return.',
        }
        return_url = reverse(
            'cangxu-material-issue-return-stock', kwargs={'pk': issue.data['id']}
        )
        returned = self.post(return_url, return_data, expected_code=201)
        line.refresh_from_db()
        issued_stock.refresh_from_db()
        self.assertEqual(line.consumed, 2)
        self.assertEqual(issued_stock.quantity, 2)
        self.assertEqual(issued_stock.consumed_by_id, build.pk)
        returned_stock = StockItem.objects.get(parent=issued_stock)
        self.assertEqual(returned_stock.quantity, 1)
        self.assertEqual(returned_stock.location_id, location.pk)
        self.assertIsNone(returned_stock.consumed_by_id)
        self.assertEqual(float(returned.data['returned_quantity']), 1)

        repeated_return = self.post(return_url, return_data, expected_code=200)
        self.assertEqual(float(repeated_return.data['returned_quantity']), 1)
        self.assertEqual(
            MaterialReturn.objects.filter(issue_id=issue.data['id']).count(), 1
        )
        line.refresh_from_db()
        self.assertEqual(line.consumed, 2)


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

    def test_quantity_rework_material_is_installed_and_traced(self):
        """Install quantity stock only for the matching active rework task."""
        unit = StockItem.objects.get(pk=1000)
        location = StockLocation.objects.get(pk=7)
        material_part = Part.objects.create(
            name='Cangxu synthetic non-serialized rework material',
            component=True,
            trackable=False,
        )
        material_stock = StockItem.objects.create(
            part=material_part, location=location, quantity=5
        )
        issue_response = self.post(
            reverse('cangxu-quality-issue-list'),
            {
                'reference': 'CX-QA-MAT-TEST-0001',
                'unit': unit.pk,
                'title': 'Synthetic rework material requirement',
                'severity': QualityIssue.Severity.MEDIUM,
            },
            expected_code=201,
        )
        task_response = self.post(
            reverse('cangxu-rework-task-list'),
            {'issue': issue_response.data['id'], 'title': 'Install synthetic pad'},
            expected_code=201,
        )
        config_response = self.post(
            reverse('cangxu-configuration-list'),
            {
                'unit': unit.pk,
                'kind': 'actual',
                'change_summary': 'Synthetic rework material installation',
            },
            expected_code=201,
        )
        configuration_url = reverse('cangxu-configuration-item-list')
        install_data = {
            'configuration': config_response.data['id'],
            'component': material_stock.pk,
            'position': 'THERMAL-PAD-01',
            'quantity': '2',
            'rework_task': task_response.data['id'],
        }
        self.post(configuration_url, install_data, expected_code=400)
        material_stock.refresh_from_db()
        self.assertEqual(material_stock.quantity, 5)
        self.assertIsNone(material_stock.belongs_to_id)

        for state in [QualityIssue.State.INVESTIGATING, QualityIssue.State.REWORK]:
            self.post(
                reverse(
                    'cangxu-quality-issue-transition',
                    kwargs={'pk': issue_response.data['id']},
                ),
                {'state': state},
                expected_code=200,
            )
        self.post(
            reverse(
                'cangxu-rework-task-transition', kwargs={'pk': task_response.data['id']}
            ),
            {'state': ReworkTask.State.IN_PROGRESS},
            expected_code=200,
        )
        install_response = self.post(configuration_url, install_data, expected_code=201)

        installed_material = StockItem.objects.get(
            pk=install_response.data['component']
        )
        material_stock.refresh_from_db()
        installed_material.refresh_from_db()
        self.assertEqual(material_stock.quantity, 3)
        self.assertEqual(installed_material.quantity, 2)
        self.assertEqual(installed_material.belongs_to_id, unit.pk)
        self.assertEqual(install_response.data['rework_task'], task_response.data['id'])
        self.assertEqual(
            installed_material.tracking_info.order_by('-pk').first().tracking_type,
            StockHistoryCode.INSTALLED_INTO_ASSEMBLY.value,
        )

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

    def test_manifest_list_handles_large_prefetched_package_sets(self):
        """List large manifests without expanding stock IDs into SQLite OR trees."""
        customer = Company.objects.create(
            name='Cangxu Synthetic Pagination Customer', is_customer=True
        )
        order = SalesOrder.objects.create(
            customer=customer,
            reference='CX-MANIFEST-PAGE-TEST',
            description='Synthetic large manifest pagination test',
        )
        shipment = SalesOrderShipment.objects.create(
            order=order, reference='CX-MANIFEST-PAGE-SHIP'
        )
        stock_items = list(StockItem.objects.order_by('pk')[:8])
        manifests = ShipmentManifest.objects.bulk_create([
            ShipmentManifest(shipment=shipment, package_code=f'CX-PAGE-PKG-{index:03d}')
            for index in range(150)
        ])
        ShipmentManifestLine.objects.bulk_create([
            ShipmentManifestLine(
                manifest=manifest,
                stock_item=stock_item,
                item_role='synthetic pagination fixture',
            )
            for manifest in manifests
            for stock_item in stock_items
        ])

        response = self.get(
            reverse('cangxu-manifest-list'), data={'limit': 200}, expected_code=200
        )

        self.assertEqual(response.data['count'], 150)
        self.assertEqual(len(response.data['results']), 150)

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

        for shipment in shipments:
            shipment.complete_allocations(shipment.allocations.all(), user=self.user)
            shipment.shipment_date = date.today()
            shipment.save(update_fields=['shipment_date'])

        first_manifest_lines = {
            row.stock_item_id: row for row in manifests[0].lines.all()
        }
        partial_data = {
            'manifest': manifests[0].pk,
            'idempotency_key': 'e62b57a2-b8e9-4cf5-8f12-645c43a3ee12',
            'recipient_name': 'Synthetic receiving operator',
            'is_final': False,
            'notes': 'Synthetic first delivery portion.',
            'lines': [
                {
                    'manifest_line': first_manifest_lines[units[0].pk].pk,
                    'quantity_received': '1',
                    'condition': ShipmentReceiptLine.Condition.DAMAGED,
                    'notes': 'Synthetic item damage found at partial receipt.',
                }
            ],
        }
        partial = self.post(
            reverse('cangxu-shipment-receipt-list'), partial_data, expected_code=201
        )
        replay = self.post(
            reverse('cangxu-shipment-receipt-list'), partial_data, expected_code=200
        )
        self.assertEqual(partial.data['id'], replay.data['id'])
        self.assertEqual(
            partial.data['lines'][0]['exception']['kind'],
            ShipmentReceiptException.Kind.DAMAGED,
        )
        self.assertEqual(
            ShipmentReceipt.objects.filter(manifest=manifests[0]).count(), 1
        )
        self.assertIsNone(ShipmentManifest.objects.get(pk=manifests[0].pk).signed_at)

        final_data = {
            'manifest': manifests[0].pk,
            'idempotency_key': 'e11a30e3-e6f7-419d-9dc2-17d6ddae3321',
            'recipient_name': 'Synthetic receiving operator',
            'is_final': True,
            'notes': 'Synthetic package accepted.',
            'lines': [
                {
                    'manifest_line': first_manifest_lines[configured_component.pk].pk,
                    'quantity_received': '1',
                }
            ],
        }
        final = self.post(
            reverse('cangxu-shipment-receipt-list'), final_data, expected_code=201
        )
        self.assertEqual(final.data['is_final'], True)
        self.assertEqual(final.data['received_by'], self.user.pk)
        self.assertEqual(len(final.data['lines']), 1)
        first_manifest_exception = ShipmentReceiptException.objects.get(
            receipt_line__receipt__manifest=manifests[0]
        )
        self.assertEqual(
            first_manifest_exception.kind, ShipmentReceiptException.Kind.DAMAGED
        )
        signed_manifest = ShipmentManifest.objects.get(pk=manifests[0].pk)
        self.assertIsNotNone(signed_manifest.signed_at)
        self.assertEqual(signed_manifest.signed_by_id, self.user.pk)

        short_final = self.post(
            reverse('cangxu-shipment-receipt-list'),
            {
                'manifest': manifests[1].pk,
                'idempotency_key': '0bd92f63-e674-49f5-9b83-cdd88cc67080',
                'recipient_name': 'Synthetic receiving operator',
                'is_final': True,
                'notes': 'Synthetic package was not received.',
                'lines': [],
            },
            expected_code=201,
        )
        self.assertEqual(len(short_final.data['lines']), 1)
        self.assertEqual(
            short_final.data['lines'][0]['exception']['kind'],
            ShipmentReceiptException.Kind.SHORT,
        )
        exception_id = short_final.data['lines'][0]['exception']['id']
        open_for_shipment = self.get(
            reverse('cangxu-receipt-exception-list'),
            data={
                'receipt_line__receipt__manifest__shipment': shipments[1].pk,
                'state': ShipmentReceiptException.State.OPEN,
            },
        )
        self.assertEqual(len(open_for_shipment.data), 1)
        self.assertEqual(open_for_shipment.data[0]['id'], exception_id)
        resolved = self.post(
            reverse('cangxu-receipt-exception-resolve', kwargs={'pk': exception_id}),
            {'resolution': 'Synthetic replacement shipment scheduled.'},
            expected_code=200,
        )
        self.assertEqual(
            resolved.data['state'], ShipmentReceiptException.State.RESOLVED
        )
        self.assertEqual(resolved.data['resolved_by'], self.user.pk)
        self.assertEqual(order.lines.get().shipped, 2)


class CangxuEndToEndManufacturingWorkflowTest(CangxuAPITestCase):
    """Verify that native purchasing, manufacturing, delivery, and RMA stay linked."""

    def test_received_component_is_built_shipped_signed_and_returned(self):
        """Trace one synthetic unit from a supplier receipt through customer return."""
        location = StockLocation.objects.get(pk=7)
        assembly = Part.objects.create(
            name='Synthetic GPU server', assembly=True, trackable=True
        )
        supplier = Company.objects.create(
            name='Cangxu Synthetic E2E Supplier', is_supplier=True
        )
        component_part = Part.objects.create(
            name='Synthetic PCIe switch card', component=True, trackable=True
        )
        BomItem.objects.create(part=assembly, sub_part=component_part, quantity=1)
        # Reuse the known untracked fixture part used by the dedicated
        # consumable issue API test to avoid introducing another MPTT tree
        # root into this workflow fixture.
        consumable_part = Part.objects.get(pk=1)
        consumable_bom = BomItem.objects.create(
            part=assembly, sub_part=consumable_part, quantity=3, consumable=True
        )
        consumable_stock = StockItem.objects.create(
            part=consumable_part, location=location, quantity=5
        )
        supplier_part = SupplierPart.objects.create(
            part=component_part, supplier=supplier, SKU='CX-E2E-SUPPLIER-001'
        )
        purchase_order = PurchaseOrder.objects.create(
            supplier=supplier, reference='CX-E2E-PO-0001'
        )
        purchase_line = PurchaseOrderLineItem.objects.create(
            order=purchase_order, part=supplier_part, quantity=1
        )
        purchase_order.place_order()
        purchase_order.receive_line_item(
            purchase_line,
            location,
            1,
            self.user,
            status=StockStatus.OK.value,
            batch_code='CX-E2E-LOT-0001',
            serials=['CX-E2E-COMP-0001'],
        )
        component = StockItem.objects.get(
            purchase_order=purchase_order, serial='CX-E2E-COMP-0001'
        )

        lot_response = self.post(
            reverse('cangxu-lot-list'),
            {
                'part': component_part.pk,
                'code': 'CX-E2E-LOT-0001',
                'purchase_order_line': purchase_line.pk,
            },
            expected_code=201,
        )
        self.post(
            reverse('cangxu-lot-stock-item-list'),
            {'lot': lot_response.data['id'], 'stock_item': component.pk},
            expected_code=201,
        )

        build = Build.objects.create(
            part=assembly,
            reference=generate_next_build_reference(),
            quantity=1,
            title='Synthetic Cangxu end-to-end build',
        )
        consumable_line = build.build_lines.get(bom_item=consumable_bom)
        issue = self.post(
            reverse('cangxu-material-issue-list'),
            {
                'build_line': consumable_line.pk,
                'stock_item': consumable_stock.pk,
                'quantity': '3',
                'idempotency_key': '4b692f74-d3a3-49d9-90bf-e91e40e35f5f',
                'notes': 'Synthetic consumable material issued to the build.',
            },
            expected_code=201,
        )
        issued_stock = StockItem.objects.get(pk=issue.data['consumed_stock_item'])
        consumable_stock.refresh_from_db()
        consumable_line.refresh_from_db()
        self.assertEqual(consumable_stock.quantity, 2)
        self.assertEqual(issued_stock.quantity, 3)
        self.assertEqual(consumable_line.consumed, 3)

        unit = build.create_build_output(
            1, serials=['CX-E2E-UNIT-0001'], user=self.user, location=location
        ).first()
        build_line = build.build_lines.get(bom_item__sub_part=component_part)
        self.post(
            reverse('api-build-allocate', kwargs={'pk': build.pk}),
            {
                'items': [
                    {
                        'build_line': build_line.pk,
                        'stock_item': component.pk,
                        'quantity': 1,
                        'output': unit.pk,
                    }
                ]
            },
            expected_code=201,
        )
        self.post(
            reverse('api-build-output-complete', kwargs={'pk': build.pk}),
            {
                'outputs': [{'output': unit.pk}],
                'location': location.pk,
                'status': StockStatus.OK.value,
            },
            expected_code=200,
        )
        returned = self.post(
            reverse(
                'cangxu-material-issue-return-stock', kwargs={'pk': issue.data['id']}
            ),
            {
                'quantity': '1',
                'location': location.pk,
                'idempotency_key': 'ab8f0c9a-723a-4ee5-a92b-b87c7adf9e6c',
                'notes': 'Synthetic unused material returned to stock.',
            },
            expected_code=201,
        )
        consumable_line.refresh_from_db()
        issued_stock.refresh_from_db()
        returned_stock = StockItem.objects.get(parent=issued_stock)
        consumable_stock.refresh_from_db()
        self.assertEqual(returned.data['id'], issue.data['id'])
        self.assertEqual(consumable_line.consumed, 2)
        self.assertEqual(issued_stock.quantity, 2)
        self.assertEqual(returned_stock.quantity, 1)
        self.assertEqual(returned_stock.location_id, location.pk)
        self.assertEqual(consumable_stock.quantity, 2)

        config_response = self.post(
            reverse('cangxu-configuration-list'),
            {'unit': unit.pk, 'change_summary': 'Synthetic E2E assembly.'},
            expected_code=201,
        )
        self.post(
            reverse('cangxu-configuration-item-list'),
            {
                'configuration': config_response.data['id'],
                'component': component.pk,
                'position': 'PCIe switch slot 01',
                'quantity': 1,
            },
            expected_code=201,
        )
        self.post(
            reverse(
                'cangxu-configuration-release',
                kwargs={'pk': config_response.data['id']},
            ),
            {},
            expected_code=200,
        )

        customer = Company.objects.create(
            name='Cangxu Synthetic E2E Customer', is_customer=True
        )
        sales_order = SalesOrder.objects.create(
            customer=customer, reference='CX-E2E-SO-0001'
        )
        sales_line = SalesOrderLineItem.objects.create(
            order=sales_order, part=assembly, quantity=1
        )
        shipment = SalesOrderShipment.objects.create(
            order=sales_order, reference='CX-E2E-SHIP-0001'
        )
        SalesOrderAllocation.objects.create(
            line=sales_line, shipment=shipment, item=unit, quantity=1
        )
        manifest_response = self.post(
            reverse('cangxu-manifest-list'),
            {
                'shipment': shipment.pk,
                'package_code': 'CX-E2E-PACKAGE-0001',
                'configuration': config_response.data['id'],
            },
            expected_code=201,
        )
        manifest_id = manifest_response.data['id']
        unit_manifest_line = self.post(
            reverse('cangxu-manifest-line-list'),
            {'manifest': manifest_id, 'stock_item': unit.pk, 'item_role': 'server'},
            expected_code=201,
        )
        component_manifest_line = self.post(
            reverse('cangxu-manifest-line-list'),
            {
                'manifest': manifest_id,
                'stock_item': component.pk,
                'item_role': 'PCIe switch card',
            },
            expected_code=201,
        )
        self.post(
            reverse('cangxu-manifest-verify', kwargs={'pk': manifest_id}),
            {},
            expected_code=200,
        )
        shipment.complete_allocations(shipment.allocations.all(), user=self.user)
        shipment.shipment_date = date.today()
        shipment.save(update_fields=['shipment_date'])
        unit.refresh_from_db()
        shipped_unit_state = (unit.location_id, unit.customer_id, unit.status)

        receipt = self.post(
            reverse('cangxu-shipment-receipt-list'),
            {
                'manifest': manifest_id,
                'idempotency_key': '42484b3e-6ee8-4d77-b59b-89d67653ea10',
                'recipient_name': 'Synthetic receiving operator',
                'is_final': True,
                'lines': [
                    {
                        'manifest_line': unit_manifest_line.data['id'],
                        'quantity_received': '1',
                    },
                    {
                        'manifest_line': component_manifest_line.data['id'],
                        'quantity_received': '1',
                    },
                ],
            },
            expected_code=201,
        )
        unit.refresh_from_db()
        self.assertEqual(
            (unit.location_id, unit.customer_id, unit.status), shipped_unit_state
        )
        self.assertTrue(receipt.data['is_final'])

        service_case = self.post(
            reverse('cangxu-service-case-list'),
            {
                'reference': 'CX-E2E-RMA-0001',
                'kind': ServiceCase.Kind.CUSTOMER_RETURN,
                'customer': customer.pk,
                'unit': unit.pk,
                'source_shipment': shipment.pk,
                'description': 'Synthetic post-delivery inspection return.',
            },
            expected_code=201,
        )
        service_line = self.post(
            reverse('cangxu-service-line-list'),
            {'case': service_case.data['id'], 'stock_item': unit.pk, 'quantity': 1},
            expected_code=201,
        )
        self.post(
            reverse('cangxu-service-event-list'),
            {
                'line': service_line.data['id'],
                'event_type': ServiceCaseEvent.EventType.RECEIVED,
                'company': customer.pk,
                'to_location': location.pk,
                'quantity': 1,
                'notes': 'Synthetic returned unit received into quarantine.',
            },
            expected_code=201,
        )
        self.post(
            reverse('cangxu-service-event-list'),
            {
                'line': service_line.data['id'],
                'stock_item': unit.pk,
                'event_type': ServiceCaseEvent.EventType.INSPECTED,
                'inspection_passed': True,
                'quantity': 1,
            },
            expected_code=201,
        )
        self.post(
            reverse(
                'cangxu-service-line-resolve', kwargs={'pk': service_line.data['id']}
            ),
            {'outcome': 'no_fault', 'notes': 'Synthetic inspection passed.'},
            expected_code=200,
        )
        self.post(
            reverse(
                'cangxu-service-case-close', kwargs={'pk': service_case.data['id']}
            ),
            {},
            expected_code=200,
        )

        component.refresh_from_db()
        unit.refresh_from_db()
        self.assertEqual(
            component.cangxu_manufacturing_lots.get().code, 'CX-E2E-LOT-0001'
        )
        self.assertEqual(component.belongs_to_id, unit.pk)
        self.assertEqual(
            unit.cangxu_service_cases.get().source_shipment_id, shipment.pk
        )
        self.assertEqual(
            unit.cangxu_service_cases.get().state, ServiceCase.State.CLOSED
        )
        self.assertEqual(
            ShipmentReceipt.objects.filter(manifest_id=manifest_id).count(), 1
        )


class CangxuDemoSeedTest(CangxuAPITestCase):
    """Check deterministic demo expansion and rerun behavior."""

    def test_demo_seed_scales_up_idempotently(self):
        """A larger factor adds synthetic records; repeating it adds none."""
        call_command('seed_cangxu_demo', scale_factor=1)
        hardware_profiles = HardwareProfileRevision.objects.filter(
            part__IPN__startswith='CX-DEMO-'
        )
        self.assertEqual(hardware_profiles.count(), 20)
        self.assertTrue(
            hardware_profiles.filter(state=HardwareProfileRevision.State.DRAFT).exists()
        )
        self.assertFalse(
            hardware_profiles.filter(
                state=HardwareProfileRevision.State.APPROVED
            ).exists()
        )
        family_ipns = [
            'CX-DEMO-SRV-K20-001',
            'CX-DEMO-SRV-K10-001',
            'CX-DEMO-WS-K2-001',
            'CX-DEMO-WS-K4-001',
        ]
        self.assertEqual(
            Part.objects.filter(IPN__in=family_ipns).count(), len(family_ipns)
        )
        self.assertEqual(
            StockItem.objects.filter(part__IPN__in=family_ipns).count(),
            len(family_ipns),
        )
        self.assertTrue(
            UnitConfiguration.objects.filter(
                unit__part__IPN__in=family_ipns, kind=UnitConfiguration.Kind.ACTUAL
            ).exists()
        )
        linkreal_profile = hardware_profiles.get(part__IPN='CX-DEMO-PCIESW-LR-001')
        self.assertIn('联瑞', linkreal_profile.board_manufacturer.name)
        self.assertIsNone(linkreal_profile.chip_vendor)
        self.assertEqual(
            linkreal_profile.kind, HardwareProfileRevision.Kind.PCIE_SWITCH
        )
        broadcom_profile = hardware_profiles.get(part__IPN='CX-DEMO-PEX89048-001')
        self.assertEqual(broadcom_profile.chip_vendor.name, 'Broadcom')
        self.assertEqual(broadcom_profile.specifications['lanes'], 48)
        self.assertEqual(broadcom_profile.state, HardwareProfileRevision.State.DRAFT)
        microchip_profile = hardware_profiles.get(part__IPN='CX-DEMO-PM50100B1-FEI-001')
        self.assertEqual(microchip_profile.chip_vendor.name, 'Microchip Technology')
        linkreal_product_profile = hardware_profiles.get(
            part__IPN='CX-DEMO-LRSV9500-4I-001'
        )
        self.assertEqual(linkreal_product_profile.chip_vendor.name, 'Broadcom')
        self.assertIn('联瑞', linkreal_product_profile.board_manufacturer.name)
        self.assertEqual(
            linkreal_product_profile.specifications['controller'], 'Broadcom PEX89048'
        )
        linkreal_lot = ManufacturingLot.objects.get(
            part__IPN='CX-DEMO-LRSV9500-4I-001', code='CX-DEMO-OPENING-202610'
        )
        for company_name, role in (
            (
                '深圳市联瑞电子有限公司 (LR-LINK / Linkreal)',
                ManufacturingLotPartner.Role.BOARD_MANUFACTURER,
            ),
            ('LR-LINK', ManufacturingLotPartner.Role.BOARD_BRAND),
            ('Broadcom', ManufacturingLotPartner.Role.CHIP_VENDOR),
        ):
            self.assertTrue(
                ManufacturingLotPartner.objects.filter(
                    lot=linkreal_lot, company__name=company_name, role=role
                ).exists()
            )
        self.assertFalse(
            StockItem.objects.filter(
                part__IPN__in=[
                    'CX-DEMO-PEX89048-001',
                    'CX-DEMO-PM50100B1-FEI-001',
                    'CX-DEMO-LRSV9500-4I-001',
                ]
            ).exists()
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
        initial_customer_returns = ServiceCase.objects.filter(
            reference__startswith='CX-DEMO-CUST-RMA-'
        ).count()
        self.assertEqual(initial_customer_returns, 16)
        initial_profile_issues = QualityIssue.objects.filter(
            reference__startswith='CX-DEMO-QA-SRC-'
        ).count()
        self.assertEqual(initial_profile_issues, 33)
        initial_receipts = ShipmentReceipt.objects.filter(
            manifest__shipment__order__reference__startswith='CX-DEMO-'
        ).count()
        self.assertTrue(
            SalesOrderShipment.objects.filter(
                order__reference__startswith='CX-DEMO-',
                shipment_date__isnull=False,
                delivery_date__isnull=False,
            ).exists()
        )
        self.assertTrue(
            ShipmentReceipt.objects.filter(
                manifest__shipment__order__reference__startswith='CX-DEMO-',
                is_final=True,
            ).exists()
        )
        self.assertTrue(
            ShipmentReceiptException.objects.filter(
                receipt_line__receipt__manifest__shipment__order__reference__startswith='CX-DEMO-'
            ).exists()
        )

        migrated_unit = StockItem.objects.filter(
            part__IPN='CX-DEMO-SRV-K20-001'
        ).first()
        expected_migrated_serial = migrated_unit.serial
        migrated_unit.serial = 'CX-DEMO-001-0001'
        migrated_unit.save(update_fields=['serial'])

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
        expanded_customer_returns = ServiceCase.objects.filter(
            reference__startswith='CX-DEMO-CUST-RMA-'
        ).count()
        expanded_profile_issues = QualityIssue.objects.filter(
            reference__startswith='CX-DEMO-QA-SRC-'
        ).count()
        expanded_receipts = ShipmentReceipt.objects.filter(
            manifest__shipment__order__reference__startswith='CX-DEMO-'
        ).count()

        self.assertGreater(expanded_stock, initial_stock)
        self.assertGreater(expanded_configurations, initial_configurations)
        self.assertGreater(expanded_service_cases, initial_service_cases)
        self.assertEqual(
            HardwareProfileRevision.objects.filter(
                part__IPN__startswith='CX-DEMO-'
            ).count(),
            20,
        )
        self.assertEqual(expanded_service_cases, 32)
        self.assertEqual(expanded_customer_returns, 32)
        self.assertEqual(expanded_profile_issues, 66)
        self.assertGreater(expanded_receipts, initial_receipts)
        migrated_unit.refresh_from_db()
        self.assertEqual(migrated_unit.serial, expected_migrated_serial)
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
        self.assertEqual(
            ServiceCase.objects.filter(
                reference__startswith='CX-DEMO-CUST-RMA-'
            ).count(),
            expanded_customer_returns,
        )
        self.assertEqual(
            QualityIssue.objects.filter(
                reference__startswith='CX-DEMO-QA-SRC-'
            ).count(),
            expanded_profile_issues,
        )
        self.assertEqual(
            ShipmentReceipt.objects.filter(
                manifest__shipment__order__reference__startswith='CX-DEMO-'
            ).count(),
            expanded_receipts,
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

    def test_historical_shipment_and_service_rows_validate_without_posting(self):
        """Validate mixed outbound/RMA history while keeping it off the stock ledger."""
        batch = self.post(
            reverse('cangxu-import-batch-list'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.SHIPMENT_HISTORY,
                'source_file_name': 'synthetic-delivery-service.xlsx',
                'source_file_digest': 'e' * 64,
            },
            expected_code=201,
        )
        batch_id = batch.data['id']
        self.post(
            reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
            [
                {
                    'source_sheet': 'Synthetic shipments',
                    'source_row': 2,
                    'source_values': {'A': {'value': 'CX-TEST-FLOW-001'}},
                    'normalized_values': {
                        'row_type': 'data',
                        'mapping_status': 'mapped',
                        'mapping_profile': 'shipment_history',
                        'fields': {
                            'product_description': 'Synthetic GPU server',
                            'quantity': 2,
                            'shipment_status': '已出库',
                            'shipped_at': '2026-10-01',
                        },
                    },
                },
                {
                    'source_sheet': 'Synthetic service',
                    'source_row': 2,
                    'source_values': {'A': {'value': 'CX-TEST-RMA-001'}},
                    'normalized_values': {
                        'row_type': 'data',
                        'mapping_status': 'mapped',
                        'mapping_profile': 'service_history',
                        'fields': {
                            'part_number': 'CX-TEST-PART-001',
                            'part_name': 'Synthetic switch board',
                            'quantity': 1,
                            'serial': 'CX-TEST-SN-001',
                            'fault_description': 'Synthetic link fault',
                            'service_status': '待检',
                        },
                    },
                },
            ],
            expected_code=201,
        )
        before_stock = StockItem.objects.count()
        validated = self.post(
            reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(validated.data['valid'], 2)
        self.assertEqual(validated.data['invalid'], 0)
        self.post(
            reverse('cangxu-import-batch-approve', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.post(
            reverse('cangxu-import-batch-apply', kwargs={'pk': batch_id}),
            {},
            expected_code=400,
        )
        self.assertEqual(StockItem.objects.count(), before_stock)
        self.assertFalse(
            DataImportRecord.objects.filter(
                batch_id=batch_id, state=DataImportRecord.State.APPLIED
            ).exists()
        )

    def test_catalog_and_receipt_rows_validate_without_posting(self):
        """Validate product and receiving history without inventing ledger entries."""
        before_stock = StockItem.objects.count()
        for index, source_kind, profile, fields in [
            (
                1,
                DataImportBatch.Kind.PART_CATALOG,
                'part_catalog',
                {
                    'part_number': 'CX-TEST-CATALOG-001',
                    'part_name': 'Synthetic GPU board',
                },
            ),
            (
                2,
                DataImportBatch.Kind.PURCHASE_HISTORY,
                'purchase_history',
                {'part_number': 'CX-TEST-RECEIPT-001', 'quantity': 3},
            ),
        ]:
            batch = self.post(
                reverse('cangxu-import-batch-list'),
                {
                    'source_system': 'CX-TEST',
                    'source_kind': source_kind,
                    'source_file_name': f'synthetic-history-{index}.xlsx',
                    'source_file_digest': str(index) * 64,
                },
                expected_code=201,
            )
            batch_id = batch.data['id']
            self.post(
                reverse('cangxu-import-batch-stage-rows', kwargs={'pk': batch_id}),
                [
                    {
                        'source_sheet': 'Synthetic source',
                        'source_row': 2,
                        'source_values': {'A': {'value': 'synthetic'}},
                        'normalized_values': {
                            'row_type': 'data',
                            'mapping_status': 'mapped',
                            'mapping_profile': profile,
                            'fields': fields,
                        },
                    }
                ],
                expected_code=201,
            )
            result = self.post(
                reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
                {},
                expected_code=200,
            )
            self.assertEqual(result.data['valid'], 1)
            self.assertEqual(result.data['invalid'], 0)
        self.assertEqual(StockItem.objects.count(), before_stock)

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
        self.assertEqual(validation.data['valid'], 1)
        self.assertEqual(validation.data['invalid'], 5)
        first_row.refresh_from_db()
        error_codes = {error['code'] for error in first_row.validation_errors}
        self.assertIn('date_missing_year', error_codes)
        self.assertIn('serial_range_quantity_mismatch', error_codes)
        unformatted_identifier_row.refresh_from_db()
        self.assertIn(
            'identifier_stored_as_number',
            {error['code'] for error in unformatted_identifier_row.validation_errors},
        )
        valid_receipt_row = DataImportRecord.objects.get(
            batch_id=batch_id, source_sheet='Synthetic inventory', source_row=3
        )
        self.assertEqual(valid_receipt_row.state, DataImportRecord.State.VALID)
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

    def test_opening_xlsx_runs_from_upload_through_native_stock_posting(self):
        """Run a synthetic opening workbook through mapping, review, and posting."""
        part = Part.objects.create(
            name='Synthetic workbook imported tracked part',
            IPN='CX-TEST-XLSX-OPEN-001',
            trackable=True,
            component=True,
        )
        location = StockLocation.objects.get(pk=7)
        workbook = Workbook()
        sheet = workbook.active
        sheet.title = 'Synthetic opening stock'
        sheet.append(['PN号', '数量', 'SN号', '本年度生产批次', '生产日期'])
        sheet.append([
            'CX-TEST-XLSX-OPEN-001',
            1,
            'CX-TEST-XLSX-SN-001',
            'CX-TEST-XLSX-LOT-001',
            '2026-10-01',
        ])
        workbook_content = BytesIO()
        workbook.save(workbook_content)

        def upload_workbook():
            return SimpleUploadedFile(
                'synthetic-opening-stock.xlsx',
                workbook_content.getvalue(),
                content_type=(
                    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                ),
            )

        before_stock = StockItem.objects.filter(part=part).count()
        uploaded = self.post(
            reverse('cangxu-import-batch-upload'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.OPENING_STOCK,
                'source_file': upload_workbook(),
                'inventory_as_of': '2026-10-01',
                'physical_count_confirmed': 'true',
            },
            expected_code=201,
            format='multipart',
        )
        self.assertEqual(uploaded.data['staged_rows'], 1)
        batch_id = uploaded.data['batch']['id']
        row = DataImportRecord.objects.get(batch_id=batch_id)
        self.assertEqual(row.source_sheet, 'Synthetic opening stock')
        self.assertEqual(row.source_row, 2)
        self.assertEqual(row.source_range, 'A2:E2')
        self.assertEqual(StockItem.objects.filter(part=part).count(), before_stock)

        mapped = self.post(
            reverse('cangxu-import-batch-map-opening-stock', kwargs={'pk': batch_id}),
            {'location': location.pk},
            expected_code=200,
        )
        self.assertEqual(mapped.data['mapped'], 1)
        row.refresh_from_db()
        self.assertEqual(row.mapped_part_id, part.pk)
        self.assertEqual(row.location_id, location.pk)

        validated = self.post(
            reverse('cangxu-import-batch-validate', kwargs={'pk': batch_id}),
            {},
            expected_code=200,
        )
        self.assertEqual(validated.data['valid'], 1)
        self.assertEqual(validated.data['invalid'], 0)
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
        self.assertEqual(StockItem.objects.filter(part=part).count(), before_stock + 1)
        row.refresh_from_db()
        self.assertEqual(row.stock_item.part_id, part.pk)
        self.assertTrue(
            ManufacturingLotStockItem.objects.filter(stock_item=row.stock_item).exists()
        )

        duplicate_upload = self.post(
            reverse('cangxu-import-batch-upload'),
            {
                'source_system': 'CX-TEST',
                'source_kind': DataImportBatch.Kind.OPENING_STOCK,
                'source_file': upload_workbook(),
                'inventory_as_of': '2026-10-01',
                'physical_count_confirmed': 'true',
            },
            expected_code=200,
            format='multipart',
        )
        self.assertEqual(duplicate_upload.data['batch']['id'], batch_id)
        self.assertEqual(duplicate_upload.data['staged_rows'], 0)
        self.assertEqual(StockItem.objects.filter(part=part).count(), before_stock + 1)

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
