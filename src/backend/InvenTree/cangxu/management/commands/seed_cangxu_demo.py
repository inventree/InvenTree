"""Load clearly synthetic server manufacturing data for local demonstrations."""

import hashlib
import json
import uuid
from datetime import date, datetime, time, timedelta
from decimal import Decimal

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from build.models import Build
from build.status_codes import BuildStatus
from build.tasks import complete_build
from build.validators import generate_next_build_reference
from cangxu.models import (
    CableEndDefinition,
    ConfigurationItem,
    CountLine,
    CountSession,
    HardwarePortDefinition,
    HardwareProfileRevision,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    PartCodeAlias,
    PurchaseReceipt,
    PurchaseReceiptInspection,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
    ShipmentReceipt,
    ShipmentReceiptException,
    ShipmentReceiptLine,
    UnitConfiguration,
)
from company.models import Company, SupplierPart
from order.models import (
    PurchaseOrder,
    PurchaseOrderLineItem,
    SalesOrder,
    SalesOrderAllocation,
    SalesOrderLineItem,
    SalesOrderShipment,
)
from order.status_codes import PurchaseOrderStatus
from order.tasks import complete_sales_order_shipment
from part.models import BomItem, Part, PartCategory
from stock.models import StockItem, StockLocation
from stock.status_codes import StockStatus

# Profile values are aggregated from the supplied workbooks. Keep only the
# row counts and coarse delivery ratio here; never load source labels, IDs,
# people, customers, serials, descriptions, or transaction rows into the seed.
DEMO_DELIVERY_CYCLE = 5
DEMO_CUSTOMER_RETURN_ROWS = 16
DEMO_PRODUCTION_ISSUE_ROWS = 33


class Command(BaseCommand):
    """Create an idempotent, synthetic product catalog and traceability sample."""

    help = 'Create fictional Cangxu server manufacturing demo records'

    @staticmethod
    def verify_synthetic_manifest(manifest):
        """Freeze the synthetic package contents before its native shipment."""
        if manifest.checked_at:
            return

        # Demo configurations are deliberately unapproved. Preserve the scanned
        # physical contents without claiming an engineering release.
        manifest.configuration = None
        lines = list(manifest.lines.select_related('stock_item', 'stock_item__part'))
        snapshot = {
            'shipment': manifest.shipment_id,
            'package_code': manifest.package_code,
            'configuration': None,
            'lines': [
                {
                    'stock_item': line.stock_item_id,
                    'part': line.stock_item.part_id,
                    'part_name': line.stock_item.part.name,
                    'serial': line.stock_item.serial,
                    'batch': line.stock_item.batch,
                    'quantity': str(line.quantity),
                    'role': line.item_role,
                }
                for line in sorted(lines, key=lambda value: value.stock_item_id)
            ],
        }
        encoded = json.dumps(
            snapshot, ensure_ascii=False, sort_keys=True, separators=(',', ':')
        )
        manifest.contents_snapshot = snapshot
        manifest.content_hash = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        manifest.checked_at = timezone.now()
        manifest.save(
            update_fields=[
                'configuration',
                'contents_snapshot',
                'content_hash',
                'checked_at',
            ]
        )

    @staticmethod
    def record_synthetic_final_receipt(manifest, received_at, variation_index):
        """Record a final fictional receipt and deterministic discrepancy sample."""
        if manifest.signed_at:
            return

        manifest_lines = list(manifest.lines.order_by('pk'))
        if not manifest_lines:
            return

        # The source workbook contains signed and incomplete delivery records.
        # Add a small, clearly labeled variance sample for exception workflow QA.
        discrepancy = (variation_index // 20) % 3 if variation_index % 20 == 0 else None
        discrepancy_by_index = {
            0: ShipmentReceiptLine.Condition.SHORT,
            1: ShipmentReceiptLine.Condition.DAMAGED,
            2: ShipmentReceiptLine.Condition.WRONG_ITEM,
        }
        changed_line = (
            manifest_lines[0] if discrepancy in discrepancy_by_index else None
        )
        notes = 'Synthetic receipt fixture; not an enterprise delivery record.'
        request_lines = []
        for manifest_line in manifest_lines:
            condition = (
                discrepancy_by_index[discrepancy]
                if manifest_line == changed_line
                else ShipmentReceiptLine.Condition.OK
            )
            quantity = (
                Decimal('0')
                if condition == ShipmentReceiptLine.Condition.SHORT
                else manifest_line.quantity
            )
            line_notes = (
                'Synthetic workflow variance; investigate using the demo case.'
                if condition != ShipmentReceiptLine.Condition.OK
                else ''
            )
            request_lines.append({
                'manifest_line': manifest_line.pk,
                'quantity_received': str(quantity),
                'condition': condition,
                'notes': line_notes,
            })

        key = uuid.uuid5(uuid.NAMESPACE_URL, f'cangxu-demo-receipt:{manifest.pk}')
        request_hash_payload = {
            'manifest': manifest.pk,
            'recipient_name': 'Synthetic recipient',
            'is_final': True,
            'notes': notes,
            'lines': sorted(request_lines, key=lambda line: line['manifest_line']),
        }
        encoded = json.dumps(
            request_hash_payload, sort_keys=True, separators=(',', ':')
        )
        receipt, created = ShipmentReceipt.objects.get_or_create(
            idempotency_key=key,
            defaults={
                'manifest': manifest,
                'request_hash': hashlib.sha256(encoded.encode('utf-8')).hexdigest(),
                'recipient_name': 'Synthetic recipient',
                'is_final': True,
                'notes': notes,
                'received_at': received_at,
            },
        )
        expected_hash = hashlib.sha256(encoded.encode('utf-8')).hexdigest()
        if not created and (
            receipt.manifest_id != manifest.pk or receipt.request_hash != expected_hash
        ):
            raise ValueError(
                'Synthetic receipt idempotency key does not match payload.'
            )

        for manifest_line, request_line in zip(
            manifest_lines, request_lines, strict=True
        ):
            receipt_line, line_created = ShipmentReceiptLine.objects.get_or_create(
                receipt=receipt,
                manifest_line=manifest_line,
                defaults={
                    'quantity_received': request_line['quantity_received'],
                    'condition': request_line['condition'],
                    'notes': request_line['notes'],
                },
            )
            condition = request_line['condition']
            if line_created and condition != ShipmentReceiptLine.Condition.OK:
                kind = {
                    ShipmentReceiptLine.Condition.SHORT: ShipmentReceiptException.Kind.SHORT,
                    ShipmentReceiptLine.Condition.DAMAGED: ShipmentReceiptException.Kind.DAMAGED,
                    ShipmentReceiptLine.Condition.WRONG_ITEM: ShipmentReceiptException.Kind.WRONG_ITEM,
                }[condition]
                ShipmentReceiptException.objects.get_or_create(
                    receipt_line=receipt_line,
                    defaults={
                        'kind': kind,
                        'expected_quantity': manifest_line.quantity,
                        'received_quantity': request_line['quantity_received'],
                        'notes': request_line['notes'],
                    },
                )

        manifest.signed_at = received_at
        manifest.receipt_notes = notes
        manifest.save(update_fields=['signed_at', 'receipt_notes'])

    def add_arguments(self, parser):
        """Allow synthetic fixture volume to grow deterministically."""
        parser.add_argument(
            '--scale-factor',
            type=int,
            default=1,
            help=(
                'Scale synthetic units, stock, receipts, and service backlog (1-100). '
                'Existing records are retained when rerun at a larger scale.'
            ),
        )

    @transaction.atomic
    def handle(self, *args, **options):
        """Create repeatable demo master data, stock, configurations, and workflows."""
        scale_factor = options['scale_factor']
        if not 1 <= scale_factor <= 100:
            raise CommandError('The demo scale factor must be between 1 and 100.')

        opening_batch = 'CX-DEMO-OPENING-202610'
        production_batch = 'CX-DEMO-PRODUCTION-202610'
        receipt_batch = 'CX-DEMO-RECEIPT-202610'
        legacy_receipt_batch = 'CX-DEMO-LOT-202610'
        unit_ipns = {
            'CX-DEMO-SRV-001',
            'CX-DEMO-BOX-001',
            'CX-DEMO-WS-001',
            'CX-DEMO-SRV-K20-001',
            'CX-DEMO-SRV-K10-001',
            'CX-DEMO-WS-K2-001',
            'CX-DEMO-WS-K4-001',
        }
        category, _ = PartCategory.objects.get_or_create(
            name='CX Demo 智算服务器', parent=None
        )
        child_categories = {}
        for name in (
            '整机',
            '计算板卡',
            '交换与网络',
            '网络交换设备',
            '线缆与附件',
            '存储与供电',
        ):
            child_categories[name], _ = PartCategory.objects.get_or_create(
                name=name, parent=category
            )

        warehouse, _ = StockLocation.objects.get_or_create(
            name='CX Demo 仓库', parent=None
        )
        receiving, _ = StockLocation.objects.get_or_create(
            name='CX Demo 收货待检', parent=warehouse
        )
        supplier, _ = Company.objects.get_or_create(
            name='虚构供应商 CX Demo',
            defaults={'is_supplier': True, 'description': 'Synthetic demo supplier'},
        )

        # Public manufacturer identities exercise separate chip-vendor roles.
        # They do not claim Cangxu ownership, supply, or compatibility.
        vendor_placeholders = {}
        for name in ('Broadcom', 'Microchip Technology', 'Astera Labs'):
            vendor_placeholders[name], _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    'description': 'Public manufacturer reference for synthetic demo profiles only; no Cangxu ownership, supply, or compatibility claim.'
                },
            )

        process_partners = {}
        for key, name, role_description in (
            ('pcb', 'CX Demo 虚构 PCB 加工商', 'PCB fabrication role example'),
            ('smt', 'CX Demo 虚构 SMT 加工商', 'SMT role example'),
            ('board', 'CX Demo 虚构板卡制造商', 'board manufacturer role example'),
            ('brand', 'CX Demo 虚构板卡品牌', 'board brand role example'),
            ('oem', 'CX Demo 虚构 OEM', 'OEM role example'),
        ):
            process_partners[key], _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    'description': f'Fictional demo company; {role_description}, not a real supplier or approved source.'
                },
            )
        linkreal_board_role, _ = Company.objects.get_or_create(
            name='深圳市联瑞电子有限公司 (LR-LINK / Linkreal)',
            defaults={
                'description': (
                    'Public manufacturer reference for synthetic demo profiles only; '
                    'no Cangxu ownership, supply, or compatibility claim.'
                )
            },
        )
        linkreal_brand, _ = Company.objects.get_or_create(
            name='LR-LINK',
            defaults={
                'description': 'Public brand reference used by synthetic demo profiles only.'
            },
        )

        catalog = [
            ('CX-DEMO-CPU-001', '通用服务器 CPU(演示)', '整机', True, 5),
            ('CX-DEMO-DIMM-001', '通用内存条(演示)', '整机', True, 8),
            ('CX-DEMO-GPU-001', 'GPU 加速卡(演示)', '计算板卡', True, 8),
            ('CX-DEMO-GPUBASE-001', 'GPU 底板(演示)', '计算板卡', True, 4),
            ('CX-DEMO-X16-ADAPTER-001', 'PCIe x16 转接板(演示)', '计算板卡', True, 8),
            ('CX-DEMO-BLINDMATE-001', '盲插连接板(演示)', '计算板卡', True, 8),
            ('CX-DEMO-MIDPLANE-001', '中置板(演示)', '计算板卡', True, 6),
            ('CX-DEMO-INFER-001', '推理加速板(演示)', '计算板卡', True, 8),
            ('CX-DEMO-FANBOARD-001', '风扇控制板(演示)', '计算板卡', True, 6),
            ('CX-DEMO-DISPLAY-001', '显示接口板(演示)', '计算板卡', True, 6),
            (
                'CX-DEMO-PCIESW-001',
                'PCIe Switch 板卡(协议待确认)',
                '交换与网络',
                True,
                4,
            ),
            (
                'CX-DEMO-NVLINK-001',
                'GPU 高速互联板卡(协议与型号待工程确认)',
                '交换与网络',
                True,
                4,
            ),
            (
                'CX-DEMO-PCIESW-BC-001',
                'PCIe Switch 板卡(博通类别角色示例, 型号待核)',
                '交换与网络',
                True,
                8,
            ),
            (
                'CX-DEMO-PCIESW-LR-001',
                'PCIe Switch 板卡(联瑞类别角色示例, 型号待核)',
                '交换与网络',
                True,
                8,
            ),
            (
                'CX-DEMO-PCIESW-OTHER-001',
                'PCIe Switch 板卡(其他厂商角色示例, 型号待核)',
                '交换与网络',
                True,
                8,
            ),
            ('CX-DEMO-NIC-001', '高速网卡 HCA(演示)', '交换与网络', True, 5),
            ('CX-DEMO-DPU-001', 'DPU(演示)', '交换与网络', True, 3),
            (
                'CX-DEMO-ETHSW-001',
                'Ethernet 交换机设备(端口与协议参数待确认)',
                '网络交换设备',
                True,
                4,
            ),
            (
                'CX-DEMO-IBSW-001',
                'InfiniBand 交换机设备(端口与协议参数待确认)',
                '网络交换设备',
                True,
                4,
            ),
            (
                'CX-DEMO-RETIMER-001',
                'PCIe Riser / Retimer(演示)',
                '交换与网络',
                True,
                5,
            ),
            ('CX-DEMO-MCIO-001', 'MCIO 内部高速线(演示)', '线缆与附件', True, 10),
            ('CX-DEMO-GPUPWR-001', 'GPU 供电线束(演示)', '线缆与附件', True, 10),
            ('CX-DEMO-DAC-001', 'DAC 高速互联线(演示)', '线缆与附件', True, 10),
            ('CX-DEMO-AOC-001', 'AOC 光互联线(演示)', '线缆与附件', True, 6),
            ('CX-DEMO-FIBER-001', '光纤跳线(接口及长度待确认)', '线缆与附件', True, 12),
            (
                'CX-DEMO-BRANCH-001',
                '多分支高速线缆(端点映射待确认)',
                '线缆与附件',
                True,
                8,
            ),
            ('CX-DEMO-RJ45-001', 'RJ45 管理线(演示)', '线缆与附件', False, 20),
            ('CX-DEMO-NVME-001', 'NVMe 固态盘(演示)', '存储与供电', True, 8),
            ('CX-DEMO-PSU-001', '服务器电源 PSU(演示)', '存储与供电', True, 8),
            ('CX-DEMO-PDB-001', '电源分配板 PDB(演示)', '存储与供电', True, 4),
            ('CX-DEMO-COOL-001', '液冷 / 散热组件(演示)', '存储与供电', True, 4),
            ('CX-DEMO-CHASSIS-001', '智算服务器机箱(演示)', '整机', True, 4),
            ('CX-DEMO-BOX-001', 'GPU BOX 整机(演示)', '整机', True, 2),
            ('CX-DEMO-WS-001', 'GPU 工作站(演示)', '整机', True, 2),
            ('CX-DEMO-SRV-001', '智算服务器整机(演示)', '整机', True, 3),
            ('CX-DEMO-SRV-K20-001', 'K20 服务器系列(虚构装机样例)', '整机', True, 0),
            ('CX-DEMO-SRV-K10-001', 'K10 服务器系列(虚构装机样例)', '整机', True, 0),
            ('CX-DEMO-WS-K2-001', 'K2 工作站系列(虚构装机样例)', '整机', True, 0),
            ('CX-DEMO-WS-K4-001', 'K4 工作站系列(虚构装机样例)', '整机', True, 0),
            (
                'CX-DEMO-PEX89048-001',
                'Broadcom PEX89048 PCIe Gen5 交换芯片(公开型号示例)',
                '交换与网络',
                False,
                0,
            ),
            (
                'CX-DEMO-PM50100B1-FEI-001',
                'Microchip Switchtec PFX Gen5 PM50100B1-FEI(公开型号示例)',
                '交换与网络',
                False,
                0,
            ),
            (
                'CX-DEMO-LRSV9500-4I-001',
                '联瑞 LRSV9500-4I PCIe Gen5 MCIO 扩展卡(公开型号示例)',
                '交换与网络',
                True,
                0,
            ),
        ]

        parts = {}
        for ipn, name, category_name, trackable, _ in catalog:
            part, _ = Part.objects.get_or_create(
                IPN=ipn,
                defaults={
                    'name': name,
                    'category': child_categories[category_name],
                    'trackable': trackable,
                    'component': True,
                    'purchaseable': True,
                    'salable': category_name == '整机',
                    'testable': category_name == '整机',
                },
            )
            parts[ipn] = part
            if ipn in unit_ipns and not part.assembly:
                part.assembly = True
                part.save(update_fields=['assembly'])
            PartCodeAlias.objects.get_or_create(
                namespace=PartCodeAlias.Namespace.ERP,
                code=ipn,
                source_system='CX-DEMO',
                company=None,
                defaults={
                    'part': part,
                    'notes': 'Synthetic demo code; not an enterprise code.',
                },
            )

        # Populate revisioned, explicitly unapproved engineering examples.
        # Public product references are sourced; Cangxu compatibility and
        # purchasing/stock status remain unconfirmed. The new catalog entries
        # are synthetic examples and have no demo stock.
        hardware_profiles = [
            (
                'CX-DEMO-GPU-001',
                HardwareProfileRevision.Kind.GPU,
                HardwareProfileRevision.Protocol.UNSPECIFIED,
                HardwareProfileRevision.FormFactor.PCIE_CARD,
                None,
                'board',
                None,
            ),
            (
                'CX-DEMO-GPUBASE-001',
                HardwareProfileRevision.Kind.ACCELERATOR_BASEBOARD,
                HardwareProfileRevision.Protocol.UNSPECIFIED,
                HardwareProfileRevision.FormFactor.BASEBOARD,
                None,
                'board',
                None,
            ),
            (
                'CX-DEMO-PCIESW-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                None,
                'board',
                'PCIe',
            ),
            (
                'CX-DEMO-PCIESW-BC-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                'Broadcom',
                'board',
                'PCIe',
            ),
            (
                'CX-DEMO-PCIESW-LR-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                None,
                'linkreal',
                'PCIe',
            ),
            (
                'CX-DEMO-PCIESW-OTHER-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                'Microchip Technology',
                'board',
                'PCIe',
            ),
            (
                'CX-DEMO-PEX89048-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.CHIP,
                'Broadcom',
                None,
                None,
            ),
            (
                'CX-DEMO-PM50100B1-FEI-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.CHIP,
                'Microchip Technology',
                None,
                None,
            ),
            (
                'CX-DEMO-LRSV9500-4I-001',
                HardwareProfileRevision.Kind.PCIE_SWITCH,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.PCIE_CARD,
                'Broadcom',
                'linkreal',
                'MCIO',
            ),
            (
                'CX-DEMO-NVLINK-001',
                HardwareProfileRevision.Kind.NVLINK_SWITCH,
                HardwareProfileRevision.Protocol.NVLINK,
                HardwareProfileRevision.FormFactor.SWITCH_BOARD,
                None,
                'board',
                'NVLink',
            ),
            (
                'CX-DEMO-ETHSW-001',
                HardwareProfileRevision.Kind.ETHERNET_SWITCH,
                HardwareProfileRevision.Protocol.ETHERNET,
                HardwareProfileRevision.FormFactor.RACKMOUNT,
                None,
                None,
                'Ethernet',
            ),
            (
                'CX-DEMO-IBSW-001',
                HardwareProfileRevision.Kind.INFINIBAND_SWITCH,
                HardwareProfileRevision.Protocol.INFINIBAND,
                HardwareProfileRevision.FormFactor.RACKMOUNT,
                None,
                None,
                'InfiniBand',
            ),
            (
                'CX-DEMO-RETIMER-001',
                HardwareProfileRevision.Kind.RETIMER,
                HardwareProfileRevision.Protocol.PCIE,
                HardwareProfileRevision.FormFactor.CHIP,
                None,
                'board',
                None,
            ),
            (
                'CX-DEMO-MCIO-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.MCIO,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'MCIO',
            ),
            (
                'CX-DEMO-GPUPWR-001',
                HardwareProfileRevision.Kind.POWER_HARNESS,
                HardwareProfileRevision.Protocol.GPU_POWER,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'GPU power',
            ),
            (
                'CX-DEMO-DAC-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.ETHERNET,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'DAC',
            ),
            (
                'CX-DEMO-AOC-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.OPTICAL,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'AOC',
            ),
            (
                'CX-DEMO-FIBER-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.OPTICAL,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'Fiber',
            ),
            (
                'CX-DEMO-BRANCH-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.MCIO,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'Breakout',
            ),
            (
                'CX-DEMO-RJ45-001',
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Protocol.MANAGEMENT,
                HardwareProfileRevision.FormFactor.CABLE,
                None,
                None,
                'RJ45',
            ),
        ]
        for (
            ipn,
            kind,
            protocol,
            form_factor,
            chip_vendor_name,
            board_role,
            connector_family,
        ) in hardware_profiles:
            profile, _ = HardwareProfileRevision.objects.get_or_create(
                part=parts[ipn],
                revision='DEMO-1',
                defaults={
                    'kind': kind,
                    'protocol': protocol,
                    'form_factor': form_factor,
                    'chip_vendor': vendor_placeholders.get(chip_vendor_name),
                    'board_manufacturer': (
                        linkreal_board_role
                        if board_role == 'linkreal'
                        else process_partners.get(board_role)
                    ),
                    'specifications': {
                        'demo_only': True,
                        'engineering_status': '待工程资料确认',
                        'parameters': {},
                    },
                    'source_reference': (
                        {
                            'CX-DEMO-PEX89048-001': 'https://www.broadcom.com/products/pcie-switches-retimers/expressfabric/gen5/pex89048',
                            'CX-DEMO-PM50100B1-FEI-001': 'https://ww1.microchip.com/downloads/aemDocuments/documents/DCS/ProductDocuments/Brochures/00003776D.pdf',
                            'CX-DEMO-LRSV9500-4I-001': 'https://www.lr-link.com.cn/productshow/LRSV9500-4I.html',
                        }.get(
                            ipn,
                            'CX-DEMO fixture only; not an approved engineering source.',
                        )
                    ),
                },
            )
            desired_chip_vendor = vendor_placeholders.get(chip_vendor_name)
            desired_board_manufacturer = (
                linkreal_board_role
                if board_role == 'linkreal'
                else process_partners.get(board_role)
            )
            if profile.chip_vendor_id != getattr(
                desired_chip_vendor, 'pk', None
            ) or profile.board_manufacturer_id != getattr(
                desired_board_manufacturer, 'pk', None
            ):
                profile.chip_vendor = desired_chip_vendor
                profile.board_manufacturer = desired_board_manufacturer
                profile.save(update_fields=['chip_vendor', 'board_manufacturer'])
            sourced_specs = {
                'CX-DEMO-PEX89048-001': {
                    'manufacturer_model': 'PEX89048',
                    'generation': 'PCIe 5.0',
                    'lanes': 48,
                    'demo_only': True,
                    'engineering_status': 'Public source reference; internal engineering review required',
                },
                'CX-DEMO-PM50100B1-FEI-001': {
                    'manufacturer_model': 'PM50100B1-FEI',
                    'family': 'Switchtec PFX 100xG5',
                    'generation': 'PCIe 5.0',
                    'lanes': 100,
                    'demo_only': True,
                    'engineering_status': 'Public source reference; internal engineering review required',
                },
                'CX-DEMO-LRSV9500-4I-001': {
                    'manufacturer_model': 'LRSV9500-4I',
                    'controller': 'Broadcom PEX89048',
                    'generation': 'PCIe 5.0',
                    'host_link': 'x16',
                    'connectors': '4 x MCIO 8i',
                    'demo_only': True,
                    'engineering_status': 'Public source reference; internal engineering review required',
                },
            }.get(ipn)
            if sourced_specs and profile.specifications != sourced_specs:
                profile.specifications = sourced_specs
                profile.save(update_fields=['specifications'])
            if connector_family in {'PCIe', 'NVLink', 'Ethernet', 'InfiniBand'}:
                HardwarePortDefinition.objects.get_or_create(
                    profile=profile,
                    path='DEMO-PORT-01',
                    defaults={
                        'protocol': protocol,
                        'connector': 'DEMO-PLACEHOLDER; confirm from engineering drawing',
                        'notes': 'Synthetic port placeholder; no electrical rating is asserted.',
                    },
                )
            if profile.kind in {
                HardwareProfileRevision.Kind.CABLE,
                HardwareProfileRevision.Kind.POWER_HARNESS,
            }:
                end_count = 3 if connector_family in {'GPU power', 'Breakout'} else 2
                for end_index in range(1, end_count + 1):
                    CableEndDefinition.objects.get_or_create(
                        profile=profile,
                        label=f'DEMO-END-{end_index:02d}',
                        defaults={
                            'connector': 'DEMO-PLACEHOLDER; confirm from engineering drawing',
                            'protocol': protocol,
                            'branch_group': 'DEMO-BRANCH'
                            if end_count > 2 and end_index > 1
                            else '',
                            'lane_map': {
                                'demo_only': True,
                                'status': '待图纸确认',
                                'endpoint_index': end_index,
                            },
                            'pinout_reference': '待工程图纸确认',
                        },
                    )

        # Populate synthetic opening stock before native Build allocation uses
        # it to consume components for the first-article workflow.
        for ipn, _, _, trackable, target_quantity in catalog:
            part = parts[ipn]
            target_quantity *= scale_factor
            current_quantity = (
                StockItem.objects.filter(
                    part=part,
                    location=warehouse,
                    belongs_to__isnull=True,
                    batch=opening_batch,
                ).aggregate(total=Sum('quantity'))['total']
                or 0
            )
            missing = max(target_quantity - int(current_quantity), 0)
            if not missing:
                continue
            if trackable:
                for stock_index in range(1, missing + 1):
                    StockItem.objects.get_or_create(
                        part=part,
                        serial=f'CX-DEMO-STOCK-{ipn}-{stock_index:04d}',
                        defaults={
                            'location': warehouse,
                            'quantity': 1,
                            'batch': opening_batch,
                            'status': 10,
                        },
                    )
            else:
                StockItem.objects.get_or_create(
                    part=part,
                    batch=opening_batch,
                    location=warehouse,
                    defaults={'quantity': missing, 'status': 10},
                )

        # Four synthetic configured units demonstrate distinct product types.
        assemblies = {
            'CX-DEMO-SRV-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-PCIESW-001', 'PCIE-SWITCH-01'),
                ('CX-DEMO-NIC-001', 'NIC-01'),
                ('CX-DEMO-MCIO-001', 'MCIO-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-PSU-001', 'PSU-01'),
            ],
            'CX-DEMO-BOX-001': [
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-02'),
                ('CX-DEMO-GPUBASE-001', 'GPU-BASE-01'),
                ('CX-DEMO-NVLINK-001', 'GPU-LINK-01'),
                ('CX-DEMO-DAC-001', 'INTERCONNECT-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-BRANCH-001', 'GPU-LINK-BRANCH-01'),
                ('CX-DEMO-PDB-001', 'PDB-01'),
            ],
            'CX-DEMO-WS-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-RETIMER-001', 'PCIE-RISER-01'),
                ('CX-DEMO-NVME-001', 'NVME-01'),
                ('CX-DEMO-RJ45-001', 'MGMT-01'),
                ('CX-DEMO-FIBER-001', 'OPTICAL-LINK-01'),
            ],
            # These family labels were taken from workbook structure only.
            # Their component lists are generic workflow fixtures, not BOMs.
            'CX-DEMO-SRV-K20-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-PCIESW-BC-001', 'PCIE-SWITCH-01'),
                ('CX-DEMO-MCIO-001', 'INTERNAL-LINK-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-PSU-001', 'PSU-01'),
            ],
            'CX-DEMO-SRV-K10-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-PCIESW-LR-001', 'PCIE-SWITCH-01'),
                ('CX-DEMO-NIC-001', 'NIC-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-PSU-001', 'PSU-01'),
            ],
            'CX-DEMO-WS-K2-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-RETIMER-001', 'PCIE-RISER-01'),
                ('CX-DEMO-NVME-001', 'NVME-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-RJ45-001', 'MGMT-01'),
            ],
            'CX-DEMO-WS-K4-001': [
                ('CX-DEMO-CPU-001', 'CPU0'),
                ('CX-DEMO-DIMM-001', 'DIMM-A1'),
                ('CX-DEMO-GPU-001', 'GPU-BAY-01'),
                ('CX-DEMO-PCIESW-OTHER-001', 'PCIE-SWITCH-01'),
                ('CX-DEMO-NVME-001', 'NVME-01'),
                ('CX-DEMO-GPUPWR-001', 'GPU-PWR-01'),
                ('CX-DEMO-FIBER-001', 'OPTICAL-LINK-01'),
            ],
        }

        units = []
        for ipn, count in (
            ('CX-DEMO-SRV-001', 20 * scale_factor),
            ('CX-DEMO-BOX-001', 8 * scale_factor),
            ('CX-DEMO-WS-001', 8 * scale_factor),
            ('CX-DEMO-SRV-K20-001', scale_factor),
            ('CX-DEMO-SRV-K10-001', scale_factor),
            ('CX-DEMO-WS-K2-001', scale_factor),
            ('CX-DEMO-WS-K4-001', scale_factor),
        ):
            part = parts[ipn]
            for index in range(1, count + 1):
                serial = f'{ipn}-{index:04d}'
                unit = StockItem.objects.filter(part=part, serial=serial).first()
                if unit is None:
                    legacy_serial = f'CX-DEMO-{ipn.rsplit("-", 1)[-1]}-{index:04d}'
                    unit = StockItem.objects.filter(
                        part=part, serial=legacy_serial
                    ).first()
                    if unit:
                        # Earlier seeds shortened the unit IPN, which collides
                        # across product families when serials are globally unique.
                        unit.serial = serial
                        unit.save(update_fields=['serial'])
                if unit is None:
                    unit, _ = StockItem.objects.get_or_create(
                        part=part,
                        serial=serial,
                        defaults={
                            'location': warehouse,
                            'quantity': 1,
                            'batch': production_batch,
                            'status': 10,
                        },
                    )
                item_specs = list(assemblies[ipn])
                if ipn == 'CX-DEMO-SRV-001' and index > 2:
                    switch_parts = (
                        'CX-DEMO-PCIESW-BC-001',
                        'CX-DEMO-PCIESW-LR-001',
                        'CX-DEMO-PCIESW-OTHER-001',
                    )
                    switch_part = switch_parts[(index - 1) % len(switch_parts)]
                    item_specs = [
                        (switch_part, position)
                        if position == 'PCIE-SWITCH-01'
                        else (component_ipn, position)
                        for component_ipn, position in item_specs
                    ]
                units.append((unit, item_specs, index))

        # One clearly fictional first-article runs through InvenTree's native
        # Build/BOM allocation/output lifecycle. This BOM is workflow test data,
        # not an approved server specification or compatibility record.
        built_unit_serial = 'CX-DEMO-SRV-BLD-0001'
        built_unit_specs = list(assemblies['CX-DEMO-SRV-001'])
        built_switch_parts = (
            'CX-DEMO-PCIESW-BC-001',
            'CX-DEMO-PCIESW-LR-001',
            'CX-DEMO-PCIESW-OTHER-001',
        )
        # Keep this one workflow fixture stable across scale-factor changes;
        # the synthetic configured-unit population covers all switch classes.
        first_article_index = 20 * scale_factor + 1
        existing_first_article = StockItem.objects.filter(
            part=parts['CX-DEMO-SRV-001'], serial=built_unit_serial
        ).first()
        existing_switch = (
            StockItem.objects
            .filter(belongs_to=existing_first_article, part__IPN__in=built_switch_parts)
            .select_related('part')
            .first()
            if existing_first_article
            else None
        )
        built_switch_part = (
            existing_switch.part.IPN if existing_switch else built_switch_parts[0]
        )
        built_unit_specs = [
            (built_switch_part, position)
            if position == 'PCIE-SWITCH-01'
            else (component_ipn, position)
            for component_ipn, position in built_unit_specs
        ]
        server_part = parts['CX-DEMO-SRV-001']
        for component_ipn, _position in built_unit_specs:
            BomItem.objects.get_or_create(
                part=server_part,
                sub_part=parts[component_ipn],
                defaults={'quantity': Decimal('1')},
            )

        build_title = 'CX Demo synthetic server first-article build'
        production_build = Build.objects.filter(
            part=server_part, batch=production_batch, title=build_title
        ).first()
        if production_build is None:
            production_build = Build.objects.create(
                part=server_part,
                reference=generate_next_build_reference(),
                batch=production_batch,
                quantity=1,
                title=build_title,
            )

        built_unit = StockItem.objects.filter(
            part=server_part, serial=built_unit_serial
        ).first()
        if built_unit is None:
            built_unit = production_build.create_build_output(
                1,
                serials=[built_unit_serial],
                user=None,
                location=warehouse,
                batch=production_batch,
            ).first()
            lines_by_part = {
                line.bom_item.sub_part_id: line
                for line in production_build.build_lines.select_related(
                    'bom_item__sub_part'
                )
            }
            allocations = []
            for component_ipn, _position in built_unit_specs:
                component_part = parts[component_ipn]
                component = (
                    StockItem.objects
                    .filter(
                        part=component_part,
                        location=warehouse,
                        belongs_to__isnull=True,
                        quantity__gte=1,
                        status=StockStatus.OK.value,
                    )
                    .order_by('pk')
                    .first()
                )
                if component is None:
                    raise ValueError(
                        f'No synthetic available stock for {component_ipn} build line.'
                    )
                allocations.append({
                    'build_line': lines_by_part[component_part.pk],
                    'stock_item': component,
                    'quantity': Decimal('1'),
                    'output': built_unit,
                })

            production_build.allocate_stock(allocations)
            production_build.complete_build_output(
                built_unit,
                user=None,
                location=warehouse,
                status=StockStatus.OK.value,
                notes='Synthetic demonstration only; not a released engineering build.',
            )
            complete_build(production_build.pk, user_id=None)
            production_build.refresh_from_db()
        elif (
            built_unit.build_id != production_build.pk
            or built_unit.is_building
            or production_build.status != BuildStatus.COMPLETE.value
            or production_build.completed != 1
        ):
            raise ValueError(
                'Synthetic first-article output exists but is not linked to a completed native Build.'
            )

        if not any(unit.pk == built_unit.pk for unit, _specs, _index in units):
            units.append((built_unit, built_unit_specs, first_article_index))

        for item_index, (unit, item_specs, unit_index) in enumerate(units, 1):
            configuration, _ = UnitConfiguration.objects.get_or_create(
                unit=unit,
                revision=1,
                defaults={
                    'kind': UnitConfiguration.Kind.ACTUAL,
                    'state': UnitConfiguration.State.DRAFT,
                    'change_summary': 'Synthetic demo baseline; engineering release is intentionally pending.',
                    'created': timezone.now(),
                },
            )
            for component_index, (ipn, position) in enumerate(item_specs, 1):
                component_part = parts[ipn]
                existing_item = (
                    configuration.items
                    .filter(position=position, removed_at__isnull=True)
                    .select_related('component__part')
                    .first()
                )
                if existing_item:
                    if existing_item.component.part_id != component_part.pk:
                        raise ValueError(
                            f'Synthetic configuration slot {position} on {unit} '
                            'already contains a different part.'
                        )
                    continue
                component_serial = (
                    f'CX-DEMO-C{item_index:02d}-{component_index:02d}-{unit_index:02d}'
                )
                component = (
                    StockItem.objects
                    .filter(part=component_part, belongs_to=unit)
                    .order_by('pk')
                    .first()
                )
                if component is None:
                    component, _ = StockItem.objects.get_or_create(
                        part=component_part,
                        serial=component_serial,
                        defaults={
                            'location': receiving,
                            'quantity': 1,
                            'batch': opening_batch,
                            'status': 10,
                        },
                    )
                if component.belongs_to_id is None:
                    unit.installStockItem(
                        component,
                        1,
                        None,
                        'Synthetic demo assembly; no production record represented.',
                    )
                ConfigurationItem.objects.get_or_create(
                    configuration=configuration,
                    component=component,
                    defaults={'position': position, 'quantity': 1},
                )

        supplier_part = parts['CX-DEMO-PCIESW-001']

        supplier_switch, _ = SupplierPart.objects.get_or_create(
            part=supplier_part,
            supplier=supplier,
            SKU='CX-DEMO-SUP-PCIESW-001',
            defaults={
                'description': 'Synthetic supplier SKU; no real purchasing terms.'
            },
        )
        purchase_order, _ = PurchaseOrder.objects.get_or_create(
            reference='CX-DEMO-PO-0001',
            defaults={
                'supplier': supplier,
                'description': 'Synthetic partial receipt for inbound workflow demo.',
            },
        )
        purchase_line, _ = PurchaseOrderLineItem.objects.get_or_create(
            order=purchase_order,
            part=supplier_switch,
            defaults={'quantity': 4 * scale_factor},
        )
        purchase_quantity = max(4 * scale_factor, int(purchase_line.received))
        if purchase_line.quantity != purchase_quantity:
            purchase_line.quantity = purchase_quantity
            purchase_line.save(update_fields=['quantity'])
        if purchase_order.status in [
            PurchaseOrderStatus.PENDING,
            PurchaseOrderStatus.ON_HOLD,
        ]:
            purchase_order.place_order()
        purchase_line.refresh_from_db()
        target_received_quantity = Decimal(2 * scale_factor)
        if purchase_line.received < target_received_quantity:
            purchase_order.receive_line_item(
                purchase_line,
                receiving,
                target_received_quantity - purchase_line.received,
                user=None,
                status=StockStatus.QUARANTINED.value,
                batch_code=receipt_batch,
                note='Synthetic partial receipt awaiting inspection.',
            )

        expanded_order, _ = PurchaseOrder.objects.get_or_create(
            reference='CX-DEMO-PO-0002',
            defaults={
                'supplier': supplier,
                'description': 'Synthetic expanded receipt for lot traceability demonstration.',
            },
        )
        expanded_line, _ = PurchaseOrderLineItem.objects.get_or_create(
            order=expanded_order,
            part=supplier_switch,
            defaults={'quantity': 24 * scale_factor},
        )
        expanded_quantity = max(24 * scale_factor, int(expanded_line.received))
        if expanded_line.quantity != expanded_quantity:
            expanded_line.quantity = expanded_quantity
            expanded_line.save(update_fields=['quantity'])
        if expanded_order.status in [
            PurchaseOrderStatus.PENDING,
            PurchaseOrderStatus.ON_HOLD,
        ]:
            expanded_order.place_order()
        expanded_line.refresh_from_db()
        expanded_target = Decimal(12 * scale_factor)
        if expanded_line.received < expanded_target:
            expanded_order.receive_line_item(
                expanded_line,
                receiving,
                expanded_target - expanded_line.received,
                user=None,
                status=StockStatus.QUARANTINED.value,
                batch_code=receipt_batch,
                note='Synthetic expanded partial receipt awaiting inspection.',
            )

        # Demonstrate both receipt choices using native status changes and a
        # receipt archive record tied to each generated native StockItem set.
        for item in StockItem.objects.filter(
            purchase_order_id=expanded_order.pk, part=supplier_part
        ).select_related('location'):
            if item.status != StockStatus.OK.value:
                item.move(
                    item.location,
                    notes='Synthetic demo receipt defaulted to available stock.',
                    user=None,
                    status=StockStatus.OK.value,
                )

        for line, batch_code, receipt_status, key_name in [
            (
                purchase_line,
                legacy_receipt_batch,
                StockStatus.QUARANTINED.value,
                'CX-DEMO-INBOUND-0001',
            ),
            (
                expanded_line,
                receipt_batch,
                StockStatus.OK.value,
                'CX-DEMO-INBOUND-0002',
            ),
        ]:
            items = list(
                StockItem.objects.filter(
                    purchase_order_id=line.order_id, part=supplier_part
                ).order_by('pk')
            )
            quantity = sum((item.quantity for item in items), Decimal('0'))
            serial_numbers = [item.serial for item in items if item.serial]
            key = uuid.uuid5(uuid.NAMESPACE_URL, key_name)
            request_payload = {
                'purchase_order_line': line.pk,
                'quantity': str(quantity),
                'location': receiving.pk,
                'status': receipt_status,
                'batch_code': batch_code,
                'serial_numbers': serial_numbers,
            }
            request_hash = hashlib.sha256(
                json.dumps(
                    request_payload, sort_keys=True, separators=(',', ':')
                ).encode('utf-8')
            ).hexdigest()
            receipt, _ = PurchaseReceipt.objects.get_or_create(
                idempotency_key=key,
                defaults={
                    'request_hash': request_hash,
                    'purchase_order_line': line,
                    'location': receiving,
                    'quantity': quantity,
                    'status': receipt_status,
                    'batch_code': batch_code,
                    'serial_numbers': serial_numbers,
                    'note': 'Synthetic receipt archive for local workflow demonstration.',
                },
            )
            receipt.stock_items.set(items)
            if line == purchase_line:
                PurchaseReceiptInspection.objects.get_or_create(
                    receipt=receipt,
                    defaults={
                        'sampling_method': PurchaseReceiptInspection.SamplingMethod.FULL,
                        'sampled_quantity': quantity,
                    },
                )

        # The command owns only CX-DEMO records. Keep purchase receipts,
        # opening stock, and finished demo units in distinct traceable lots.
        for item in StockItem.objects.filter(
            part__IPN__startswith='CX-DEMO-'
        ).select_related('part'):
            if item.purchase_order_id == purchase_order.pk:
                batch = legacy_receipt_batch
            elif item.purchase_order_id == expanded_order.pk:
                batch = receipt_batch
            elif item.part.IPN in unit_ipns:
                batch = production_batch
            else:
                batch = opening_batch
            if item.batch != batch:
                item.batch = batch
                item.save(update_fields=['batch'])

        # Earlier demo revisions reassigned unit batches after creating lot links.
        # Reconcile only demo-owned links so each physical item points to the lot
        # matching its current part and batch before rebuilding the expected links.
        ManufacturingLotStockItem.objects.filter(
            stock_item__part__IPN__startswith='CX-DEMO-',
            lot__part__IPN__startswith='CX-DEMO-',
        ).exclude(
            lot__part=F('stock_item__part'), lot__code=F('stock_item__batch')
        ).delete()

        # Retire the earlier single-lot demo shape and rebuild its links using
        # explicit source, opening-stock, and production batches.
        old_lots = ManufacturingLot.objects.filter(
            part__IPN__startswith='CX-DEMO-', code='CX-DEMO-LOT-202610'
        )
        ManufacturingLotStockItem.objects.filter(lot__in=old_lots).delete()
        old_lots.delete()

        board_ipns = {
            'CX-DEMO-GPUBASE-001',
            'CX-DEMO-X16-ADAPTER-001',
            'CX-DEMO-BLINDMATE-001',
            'CX-DEMO-MIDPLANE-001',
            'CX-DEMO-INFER-001',
            'CX-DEMO-FANBOARD-001',
            'CX-DEMO-DISPLAY-001',
            'CX-DEMO-PCIESW-001',
            'CX-DEMO-PCIESW-BC-001',
            'CX-DEMO-PCIESW-LR-001',
            'CX-DEMO-PCIESW-OTHER-001',
            'CX-DEMO-LRSV9500-4I-001',
            'CX-DEMO-NVLINK-001',
            'CX-DEMO-RETIMER-001',
            'CX-DEMO-PDB-001',
        }
        chip_vendor_by_ipn = {
            'CX-DEMO-PCIESW-BC-001': 'Broadcom',
            'CX-DEMO-PCIESW-OTHER-001': 'Microchip Technology',
            'CX-DEMO-PEX89048-001': 'Broadcom',
            'CX-DEMO-PM50100B1-FEI-001': 'Microchip Technology',
            'CX-DEMO-LRSV9500-4I-001': 'Broadcom',
        }
        ManufacturingLotPartner.objects.filter(
            lot__part__IPN__startswith='CX-DEMO-',
            role=ManufacturingLotPartner.Role.CHIP_VENDOR,
            company__name__in=[
                'CX Demo 虚构厂商-博通类别',
                'CX Demo 虚构厂商-联瑞类别',
                'CX Demo 虚构厂商-其他类别',
            ],
        ).delete()
        ManufacturingLotPartner.objects.filter(
            lot__part__IPN__startswith='CX-DEMO-',
            role=ManufacturingLotPartner.Role.BOARD_MANUFACTURER,
            company__name='CX Demo 虚构板卡制造商-联瑞类别',
        ).delete()
        for ipn, part in parts.items():
            batch_codes = {opening_batch}
            if ipn in unit_ipns:
                batch_codes.add(production_batch)
            if ipn == supplier_part.IPN:
                batch_codes.add(legacy_receipt_batch)
                batch_codes.add(receipt_batch)

            for batch_code in batch_codes:
                purchase_line_link = None
                if ipn == supplier_part.IPN:
                    purchase_line_link = {
                        legacy_receipt_batch: purchase_line,
                        receipt_batch: expanded_line,
                    }.get(batch_code)
                lot, _ = ManufacturingLot.objects.get_or_create(
                    part=part,
                    code=batch_code,
                    defaults={
                        'purchase_order_line': purchase_line_link,
                        'notes': 'Synthetic demo lot; no enterprise source data or approved compatibility claim.',
                    },
                )
                if lot.purchase_order_line_id != getattr(
                    purchase_line_link, 'pk', None
                ):
                    lot.purchase_order_line = purchase_line_link
                    lot.save(update_fields=['purchase_order_line'])

                if purchase_line_link:
                    ManufacturingLotPartner.objects.get_or_create(
                        lot=lot,
                        company=supplier,
                        role=ManufacturingLotPartner.Role.SUPPLIER,
                    )
                if ipn in board_ipns:
                    for key, role in (
                        ('pcb', ManufacturingLotPartner.Role.PCB),
                        ('smt', ManufacturingLotPartner.Role.SMT),
                    ):
                        ManufacturingLotPartner.objects.get_or_create(
                            lot=lot, company=process_partners[key], role=role
                        )
                    board_manufacturer = (
                        linkreal_board_role
                        if ipn == 'CX-DEMO-LRSV9500-4I-001'
                        else process_partners['board']
                    )
                    ManufacturingLotPartner.objects.get_or_create(
                        lot=lot,
                        company=board_manufacturer,
                        role=ManufacturingLotPartner.Role.BOARD_MANUFACTURER,
                    )
                    board_brand = (
                        linkreal_brand
                        if ipn == 'CX-DEMO-LRSV9500-4I-001'
                        else process_partners['brand']
                    )
                    ManufacturingLotPartner.objects.get_or_create(
                        lot=lot,
                        company=board_brand,
                        role=ManufacturingLotPartner.Role.BOARD_BRAND,
                    )
                chip_vendor_name = chip_vendor_by_ipn.get(ipn)
                if chip_vendor_name:
                    ManufacturingLotPartner.objects.get_or_create(
                        lot=lot,
                        company=vendor_placeholders[chip_vendor_name],
                        role=ManufacturingLotPartner.Role.CHIP_VENDOR,
                    )
                if ipn in unit_ipns:
                    ManufacturingLotPartner.objects.get_or_create(
                        lot=lot,
                        company=process_partners['oem'],
                        role=ManufacturingLotPartner.Role.OEM,
                    )

                stock_items = StockItem.objects.filter(part=part, batch=batch_code)
                for item in stock_items.iterator():
                    ManufacturingLotStockItem.objects.get_or_create(
                        lot=lot, stock_item=item
                    )

        # Keep the orders and manifests pending: these are allocated sample
        # shipments, not claims that synthetic machines passed QA or shipped.
        customer, _ = Company.objects.get_or_create(
            name='虚构客户 CX Demo',
            defaults={
                'is_customer': True,
                'description': 'Synthetic demo customer; no real customer data.',
            },
        )
        sales_order, _ = SalesOrder.objects.get_or_create(
            reference='CX-DEMO-SO-0001',
            defaults={
                'customer': customer,
                'description': 'Synthetic server order with per-unit split shipments.',
            },
        )
        sales_groups = []
        for ipn, order_reference, description in (
            ('CX-DEMO-SRV-001', 'CX-DEMO-SO-0001', 'Synthetic server split shipments.'),
            (
                'CX-DEMO-BOX-001',
                'CX-DEMO-SO-BOX-0001',
                'Synthetic GPU BOX split shipments.',
            ),
            (
                'CX-DEMO-WS-001',
                'CX-DEMO-SO-WS-0001',
                'Synthetic workstation split shipments.',
            ),
            (
                'CX-DEMO-SRV-K20-001',
                'CX-DEMO-SO-K20-0001',
                'Synthetic K20-family server workflow sample; not an approved BOM.',
            ),
            (
                'CX-DEMO-SRV-K10-001',
                'CX-DEMO-SO-K10-0001',
                'Synthetic K10-family server workflow sample; not an approved BOM.',
            ),
            (
                'CX-DEMO-WS-K2-001',
                'CX-DEMO-SO-K2-0001',
                'Synthetic K2-family workstation workflow sample; not an approved BOM.',
            ),
            (
                'CX-DEMO-WS-K4-001',
                'CX-DEMO-SO-K4-0001',
                'Synthetic K4-family workstation workflow sample; not an approved BOM.',
            ),
        ):
            grouped_units = [
                record[0] for record in units if record[0].part_id == parts[ipn].pk
            ]
            if order_reference == sales_order.reference:
                order = sales_order
            else:
                order, _ = SalesOrder.objects.get_or_create(
                    reference=order_reference,
                    defaults={'customer': customer, 'description': description},
                )
            sales_line, _ = SalesOrderLineItem.objects.get_or_create(
                order=order, part=parts[ipn], defaults={'quantity': len(grouped_units)}
            )
            if sales_line.quantity < len(grouped_units):
                sales_line.quantity = len(grouped_units)
                sales_line.save(update_fields=['quantity'])
            sales_groups.append((ipn, order, sales_line, grouped_units))

        shipment_count = 0
        delivered_samples = []
        for ipn, order, sales_line, grouped_units in sales_groups:
            short_name = ipn.removeprefix('CX-DEMO-').split('-')[0]
            for shipment_index, unit in enumerate(grouped_units, 1):
                if ipn == 'CX-DEMO-SRV-001' and shipment_index <= 2:
                    shipment_reference = f'CX-DEMO-SHIP-{shipment_index:04d}'
                    package_code = f'CX-DEMO-PKG-{shipment_index:04d}'
                else:
                    shipment_reference = (
                        f'CX-DEMO-SHIP-{short_name}-{shipment_index:03d}'
                    )
                    package_code = f'CX-DEMO-PKG-{short_name}-{shipment_index:03d}'
                shipment, _ = SalesOrderShipment.objects.get_or_create(
                    order=order, reference=shipment_reference
                )
                SalesOrderAllocation.objects.get_or_create(
                    line=sales_line,
                    shipment=shipment,
                    item=unit,
                    defaults={'quantity': 1},
                )
                manifest, _ = ShipmentManifest.objects.get_or_create(
                    shipment=shipment,
                    package_code=package_code,
                    defaults={
                        'configuration': unit.cangxu_configurations.filter(
                            kind=UnitConfiguration.Kind.ACTUAL
                        ).first()
                    },
                )
                ShipmentManifestLine.objects.get_or_create(
                    manifest=manifest,
                    stock_item=unit,
                    defaults={'quantity': 1, 'item_role': '整机'},
                )
                for component in unit.installed_parts.all():
                    ShipmentManifestLine.objects.get_or_create(
                        manifest=manifest,
                        stock_item=component,
                        defaults={'quantity': 1, 'item_role': '装机配件'},
                    )
                # The workbook has a mix of shipped, pending, and unspecified
                # delivery rows. Keep roughly four fifths as completed samples
                # and retain pending allocations for the remaining workflow.
                if shipment_index % DEMO_DELIVERY_CYCLE != 0:
                    self.verify_synthetic_manifest(manifest)
                    shipment.refresh_from_db()
                    if not shipment.shipment_date and shipment.check_can_complete(
                        raise_error=False
                    ):
                        shipped_date = date(2025, 1, 1) + timedelta(
                            days=(shipment.pk * 29) % 580
                        )
                        delivered_date = shipped_date + timedelta(
                            days=(shipment.pk % 6) + 1
                        )
                        complete_sales_order_shipment(
                            shipment.pk,
                            None,
                            shipped_date.isoformat(),
                            delivery_date=delivered_date.isoformat(),
                        )
                        shipment.refresh_from_db()
                    if shipment.shipment_date:
                        received_at = datetime.combine(
                            shipment.delivery_date or shipment.shipment_date,
                            time(hour=12),
                        )
                        if settings.USE_TZ:
                            received_at = timezone.make_aware(received_at)
                        self.record_synthetic_final_receipt(
                            manifest, received_at, shipment_count
                        )
                        delivered_samples.append((unit, shipment))
                shipment_count += 1

        service_item_ipns = [
            'CX-DEMO-GPU-001',
            'CX-DEMO-GPUBASE-001',
            'CX-DEMO-INFER-001',
            'CX-DEMO-PCIESW-BC-001',
            'CX-DEMO-PCIESW-LR-001',
            'CX-DEMO-PCIESW-OTHER-001',
            'CX-DEMO-X16-ADAPTER-001',
            'CX-DEMO-MIDPLANE-001',
        ]
        for case_index in range(1, DEMO_CUSTOMER_RETURN_ROWS * scale_factor + 1):
            repair = case_index % 2 == 1
            case, _ = ServiceCase.objects.get_or_create(
                reference=f'CX-DEMO-RMA-{case_index:04d}',
                defaults={
                    'kind': (
                        ServiceCase.Kind.SUPPLIER_REPAIR
                        if repair
                        else ServiceCase.Kind.INTERNAL_FAILURE
                    ),
                    'supplier': supplier if repair else None,
                    'description': (
                        'Synthetic service backlog record; no real customer, '
                        'supplier incident, or defect is represented.'
                    ),
                },
            )
            if case.lines.exists():
                continue
            repair_item = (
                StockItem.objects
                .filter(
                    part__IPN__in=service_item_ipns,
                    location=warehouse,
                    belongs_to__isnull=True,
                    batch=opening_batch,
                    quantity__gte=1,
                    status=StockStatus.OK.value,
                    sales_order__isnull=True,
                    cangxu_service_lines__isnull=True,
                )
                .select_related('part')
                .order_by('pk')
                .first()
            )
            if repair_item is None:
                break
            ServiceCaseLine.objects.get_or_create(
                case=case,
                stock_item=repair_item,
                defaults={
                    'quantity': 1,
                    'fault_description': (
                        'Synthetic service record; inspect and classify before action.'
                    ),
                },
            )

        # The after-sales workbook has a separate row set from the open supplier
        # repair/internal backlog. Expand that shape into customer-return cases
        # linked to a shipped synthetic unit and its native source shipment.
        customer_return_count = DEMO_CUSTOMER_RETURN_ROWS * scale_factor
        if len(delivered_samples) < customer_return_count:
            raise CommandError(
                'Not enough completed synthetic shipments to seed customer returns.'
            )
        for case_index, (unit, shipment) in enumerate(
            delivered_samples[:customer_return_count], 1
        ):
            case, _ = ServiceCase.objects.get_or_create(
                reference=f'CX-DEMO-CUST-RMA-{case_index:05d}',
                defaults={
                    'kind': ServiceCase.Kind.CUSTOMER_RETURN,
                    'customer': customer,
                    'source_shipment': shipment,
                    'unit': unit,
                    'description': (
                        'Synthetic customer-return record derived from workbook '
                        'row shape; no real customer, SN, failure, or outcome.'
                    ),
                },
            )
            if (
                case.kind != ServiceCase.Kind.CUSTOMER_RETURN
                or case.customer_id != customer.pk
                or case.source_shipment_id != shipment.pk
                or case.unit_id != unit.pk
            ):
                case.kind = ServiceCase.Kind.CUSTOMER_RETURN
                case.customer = customer
                case.supplier = None
                case.source_shipment = shipment
                case.unit = unit
                case.save(
                    update_fields=[
                        'kind',
                        'customer',
                        'supplier',
                        'source_shipment',
                        'unit',
                    ]
                )
            ServiceCaseLine.objects.get_or_create(
                case=case,
                stock_item=unit,
                defaults={
                    'quantity': 1,
                    'fault_description': (
                        'Synthetic return intake pending; physical custody and '
                        'inspection have not been recorded.'
                    ),
                },
            )

        first_unit = units[0][0]
        issue, _ = QualityIssue.objects.get_or_create(
            reference='CX-DEMO-QA-0001',
            defaults={
                'unit': first_unit,
                'component': first_unit.installed_parts.first(),
                'title': 'Synthetic GPU thermal check follow-up',
                'description': 'Demonstration-only issue; no real defect or field incident.',
                'severity': QualityIssue.Severity.MEDIUM,
                'containment': 'Hold for synthetic verification.',
            },
        )
        ReworkTask.objects.get_or_create(
            issue=issue,
            title='Synthetic recheck GPU cooling path',
            defaults={
                'instructions': 'Demo task only; use approved engineering work instructions in production.'
            },
        )

        # The production workbook contains a separate issue log. Expand its row
        # shape into synthetic quality observations without copying descriptions,
        # causes, operators, dates, or source references.
        unit_ids = [unit.pk for unit, _specs, _index in units]
        components_by_unit = {}
        for component in (
            StockItem.objects
            .filter(belongs_to_id__in=unit_ids)
            .select_related('part')
            .order_by('pk')
        ):
            components_by_unit.setdefault(component.belongs_to_id, []).append(component)
        issue_states = (
            QualityIssue.State.OPEN,
            QualityIssue.State.INVESTIGATING,
            QualityIssue.State.REWORK,
            QualityIssue.State.VERIFY,
            QualityIssue.State.CLOSED,
        )
        issue_titles = (
            'Synthetic visual inspection follow-up',
            'Synthetic cable routing recheck',
            'Synthetic functional test observation',
            'Synthetic board fit review',
        )
        issue_count = DEMO_PRODUCTION_ISSUE_ROWS * scale_factor
        now = timezone.now()
        for issue_index in range(1, issue_count + 1):
            unit = units[(issue_index - 1) % len(units)][0]
            unit_components = components_by_unit.get(unit.pk, [])
            component = (
                unit_components[(issue_index - 1) % len(unit_components)]
                if unit_components
                else None
            )
            state = issue_states[(issue_index - 1) % len(issue_states)]
            detected_at = now - timedelta(days=(issue_index * 7) % 365)
            issue, _ = QualityIssue.objects.get_or_create(
                reference=f'CX-DEMO-QA-SRC-{issue_index:05d}',
                defaults={
                    'unit': unit,
                    'component': component,
                    'title': issue_titles[(issue_index - 1) % len(issue_titles)],
                    'description': (
                        'Synthetic production issue profile; no source defect, '
                        'employee, customer, or disposition is represented.'
                    ),
                    'severity': list(QualityIssue.Severity)[
                        (issue_index - 1) % len(QualityIssue.Severity)
                    ],
                    'state': state,
                    'containment': 'Synthetic demo containment; validate locally.',
                    'detected_at': detected_at,
                    'closed_at': (
                        detected_at + timedelta(days=2)
                        if state == QualityIssue.State.CLOSED
                        else None
                    ),
                    'verification_notes': (
                        'Synthetic verification sample.'
                        if state == QualityIssue.State.CLOSED
                        else ''
                    ),
                },
            )
            if state in {QualityIssue.State.REWORK, QualityIssue.State.VERIFY}:
                ReworkTask.objects.get_or_create(
                    issue=issue,
                    title=f'Synthetic production correction {issue_index:05d}',
                    defaults={
                        'instructions': (
                            'Synthetic workflow fixture; replace with approved '
                            'work instructions before production use.'
                        ),
                        'state': (
                            ReworkTask.State.VERIFY
                            if state == QualityIssue.State.VERIFY
                            else ReworkTask.State.IN_PROGRESS
                        ),
                    },
                )

        count, _ = CountSession.objects.get_or_create(
            reference='CX-DEMO-COUNT-0001',
            defaults={
                'location': warehouse,
                'notes': 'Synthetic open count session; no automatic stock adjustment.',
            },
        )
        for stock_item in StockItem.objects.filter(
            location=warehouse, part__IPN__startswith='CX-DEMO-'
        ):
            CountLine.objects.get_or_create(
                session=count,
                stock_item=stock_item,
                defaults={
                    'part': stock_item.part,
                    'expected_quantity': stock_item.quantity,
                },
            )

        demo_shipments = SalesOrderShipment.objects.filter(
            order__reference__startswith='CX-DEMO-'
        )
        completed_shipment_count = demo_shipments.filter(
            shipment_date__isnull=False
        ).count()
        pending_shipment_count = demo_shipments.filter(
            shipment_date__isnull=True
        ).count()

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded synthetic Cangxu demo catalog: {len(parts)} parts, '
                f'{StockItem.objects.filter(part__IPN__startswith="CX-DEMO-").count()} stock items, '
                f'{len(units)} configured units, '
                f'{ManufacturingLotStockItem.objects.filter(stock_item__part__IPN__startswith="CX-DEMO-").count()} lot links, '
                f'{completed_shipment_count} completed / '
                f'{pending_shipment_count} pending split shipments, '
                f'{ShipmentReceipt.objects.filter(manifest__shipment__order__reference__startswith="CX-DEMO-").count()} final receipts, '
                f'{ShipmentReceiptException.objects.filter(receipt_line__receipt__manifest__shipment__order__reference__startswith="CX-DEMO-").count()} receipt exceptions, '
                f'{ServiceCase.objects.filter(reference__startswith="CX-DEMO-RMA-").count()} supplier/internal service cases, '
                f'{ServiceCase.objects.filter(reference__startswith="CX-DEMO-CUST-RMA-").count()} customer-return cases, '
                f'{QualityIssue.objects.filter(reference__startswith="CX-DEMO-QA-SRC-").count()} synthetic production issues.'
            )
        )
