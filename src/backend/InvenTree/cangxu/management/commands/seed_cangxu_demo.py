"""Load clearly synthetic server manufacturing data for local demonstrations."""

from decimal import Decimal

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.db.models import F, Sum
from django.utils import timezone

from build.models import Build
from build.status_codes import BuildStatus
from build.tasks import complete_build
from build.validators import generate_next_build_reference
from cangxu.models import (
    ConfigurationItem,
    CountLine,
    CountSession,
    ManufacturingLot,
    ManufacturingLotPartner,
    ManufacturingLotStockItem,
    PartCodeAlias,
    QualityIssue,
    ReworkTask,
    ServiceCase,
    ServiceCaseLine,
    ShipmentManifest,
    ShipmentManifestLine,
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
from part.models import BomItem, Part, PartCategory
from stock.models import StockItem, StockLocation
from stock.status_codes import StockStatus


class Command(BaseCommand):
    """Create an idempotent, synthetic product catalog and traceability sample."""

    help = 'Create fictional Cangxu server manufacturing demo records'

    def add_arguments(self, parser):
        """Allow synthetic fixture volume to grow deterministically."""
        parser.add_argument(
            '--scale-factor',
            type=int,
            default=1,
            help=(
                'Multiply demo unit counts, opening stock, and receipt quantities '
                '(1-100). Existing records are retained when rerun at a larger scale.'
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
        unit_ipns = {'CX-DEMO-SRV-001', 'CX-DEMO-BOX-001', 'CX-DEMO-WS-001'}
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

        # These fictional companies demonstrate distinct chip-vendor roles.
        # They do not claim real products, supply relationships, or compatibility.
        vendor_placeholders = {}
        for name in (
            'CX Demo 虚构厂商-博通类别',
            'CX Demo 虚构厂商-联瑞类别',
            'CX Demo 虚构厂商-其他类别',
        ):
            vendor_placeholders[name], _ = Company.objects.get_or_create(
                name=name,
                defaults={
                    'description': 'Fictional role fixture only; no real product, model, supply, protocol, or compatibility claim.'
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

        catalog = [
            ('CX-DEMO-CPU-001', '通用服务器 CPU(演示)', '整机', True, 5),
            ('CX-DEMO-DIMM-001', '通用内存条(演示)', '整机', True, 8),
            ('CX-DEMO-GPU-001', 'GPU 加速卡(演示)', '计算板卡', True, 8),
            ('CX-DEMO-GPUBASE-001', 'GPU 底板(演示)', '计算板卡', True, 4),
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
        }

        units = []
        for ipn, count in (
            ('CX-DEMO-SRV-001', 20 * scale_factor),
            ('CX-DEMO-BOX-001', 8 * scale_factor),
            ('CX-DEMO-WS-001', 8 * scale_factor),
        ):
            part = parts[ipn]
            for index in range(1, count + 1):
                serial = f'CX-DEMO-{ipn.rsplit("-", 1)[-1]}-{index:04d}'
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

        for placeholder in vendor_placeholders.values():
            placeholder.description = (
                'Synthetic demo placeholder; identity, product model, protocol, '
                'and role must be confirmed from approved engineering records.'
            )
            placeholder.save(update_fields=['description'])

        # Retire the earlier single-lot demo shape and rebuild its links using
        # explicit source, opening-stock, and production batches.
        old_lots = ManufacturingLot.objects.filter(
            part__IPN__startswith='CX-DEMO-', code='CX-DEMO-LOT-202610'
        )
        ManufacturingLotStockItem.objects.filter(lot__in=old_lots).delete()
        old_lots.delete()

        board_ipns = {
            'CX-DEMO-GPUBASE-001',
            'CX-DEMO-PCIESW-001',
            'CX-DEMO-PCIESW-BC-001',
            'CX-DEMO-PCIESW-LR-001',
            'CX-DEMO-PCIESW-OTHER-001',
            'CX-DEMO-NVLINK-001',
            'CX-DEMO-RETIMER-001',
            'CX-DEMO-PDB-001',
        }
        chip_vendor_by_ipn = {
            'CX-DEMO-PCIESW-BC-001': 'CX Demo 虚构厂商-博通类别',
            'CX-DEMO-PCIESW-LR-001': 'CX Demo 虚构厂商-联瑞类别',
            'CX-DEMO-PCIESW-OTHER-001': 'CX Demo 虚构厂商-其他类别',
        }
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
                        ('board', ManufacturingLotPartner.Role.BOARD_MANUFACTURER),
                        ('brand', ManufacturingLotPartner.Role.BOARD_BRAND),
                    ):
                        ManufacturingLotPartner.objects.get_or_create(
                            lot=lot, company=process_partners[key], role=role
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
                shipment_count += 1

        repair_item = StockItem.objects.filter(
            part=supplier_part,
            location=warehouse,
            belongs_to__isnull=True,
            batch=opening_batch,
        ).first()
        if repair_item:
            repair_case, _ = ServiceCase.objects.get_or_create(
                reference='CX-DEMO-RMA-0001',
                defaults={
                    'kind': ServiceCase.Kind.SUPPLIER_REPAIR,
                    'supplier': supplier,
                    'description': 'Synthetic supplier repair case awaiting outbound inspection.',
                },
            )
            ServiceCaseLine.objects.get_or_create(
                case=repair_case,
                stock_item=repair_item,
                defaults={
                    'quantity': 1,
                    'fault_description': 'Synthetic demonstration case; no real defect.',
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

        self.stdout.write(
            self.style.SUCCESS(
                f'Loaded synthetic Cangxu demo catalog: {len(parts)} parts, '
                f'{StockItem.objects.filter(part__IPN__startswith="CX-DEMO-").count()} stock items, '
                f'{len(units)} configured units, '
                f'{ManufacturingLotStockItem.objects.filter(stock_item__part__IPN__startswith="CX-DEMO-").count()} lot links, '
                f'{shipment_count} pending split shipments.'
            )
        )
