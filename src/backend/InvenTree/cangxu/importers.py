"""Read-only workbook parsing helpers for staged Cangxu imports."""

from datetime import date, datetime, time

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

MAX_WORKBOOK_BYTES = 25 * 1024 * 1024
MAX_WORKBOOK_CELLS = 500_000
MAX_WORKBOOK_ROWS = 50_000

COMMON_HEADERS = {
    '数量': 'quantity',
    '数量（PCS）': 'quantity',  # noqa: RUF001 - exact source workbook header
    'SN': 'serial',
    'SN号': 'serial',
    'PN号': 'part_number',
    '料号': 'part_number',
    '本年度生产批次': 'batch_code',
    '生产日期': 'production_date',
    'BOM号': 'bom_code',
    '供应商': 'supplier_label',
}
IMPORT_HEADERS = {
    'opening_stock': {
        **COMMON_HEADERS,
        '品名': 'part_name',
        '产品名称': 'part_name',
        '产品型号': 'part_model',
        '类别': 'part_category',
        'OEM PN 号': 'oem_part_number',
        '是否到货': 'receipt_status',
    },
    'part_catalog': {
        **COMMON_HEADERS,
        '品名': 'part_name',
        '产品名称': 'part_name',
        '产品型号': 'part_model',
        '类别': 'part_category',
        'OEM PN 号': 'oem_part_number',
        '是否到货': 'receipt_status',
    },
    'purchase_history': {
        **COMMON_HEADERS,
        '品名': 'part_name',
        '产品名称': 'part_name',
        '产品型号': 'part_model',
        '类别': 'part_category',
        '是否到货': 'receipt_status',
    },
    'shipment_history': {
        '数量': 'quantity',
        '数量（PCS）': 'quantity',  # noqa: RUF001 - exact source workbook header
        '出库产品': 'product_description',
        '状态': 'shipment_status',
        '状态（已出库/未出库）': 'shipment_status',  # noqa: RUF001 - source header
        '出库时间': 'shipped_at',
        '流程编号': 'external_reference',
        '项目名称': 'project_reference',
    },
    'service_history': {
        '料号': 'part_number',
        '名称': 'part_name',
        '数量': 'quantity',
        'SN': 'serial',
        '故障原因具体描述': 'fault_description',
        '售后状态': 'service_status',
        '售后出库': 'shipped_at',
        '售后入库': 'returned_at',
        '原因': 'failure_reason',
        '备注': 'notes',
    },
}


class WorkbookImportError(ValueError):
    """Raised when an uploaded workbook cannot be safely staged."""


def _json_value(value):
    """Convert supported Excel values into stable JSON-compatible scalars."""
    if isinstance(value, (datetime, date, time)):
        return value.isoformat()
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def parse_workbook_rows(upload):
    """Return populated worksheet rows while preserving cell coordinates/format."""
    if upload.size > MAX_WORKBOOK_BYTES:
        raise WorkbookImportError('workbook_too_large')

    try:
        workbook = load_workbook(upload, read_only=True, data_only=False)
    except Exception as exc:
        raise WorkbookImportError('invalid_xlsx') from exc

    rows = []
    cell_count = 0
    try:
        for sheet in workbook.worksheets:
            for row_index, row in enumerate(sheet.iter_rows(), start=1):
                cell_count += len(row)
                if cell_count > MAX_WORKBOOK_CELLS:
                    raise WorkbookImportError('workbook_too_many_cells')

                populated = [
                    (column_index, cell)
                    for column_index, cell in enumerate(row, start=1)
                    if cell.value is not None
                ]
                if not populated:
                    continue

                values = {
                    get_column_letter(column_index): {
                        'value': _json_value(cell.value),
                        'data_type': cell.data_type,
                        'number_format': cell.number_format,
                    }
                    for column_index, cell in enumerate(row, start=1)
                }
                first_col = min(column for column, _cell in populated)
                last_col = max(column for column, _cell in populated)
                rows.append({
                    'source_sheet': sheet.title[:100],
                    'source_row': row_index,
                    'source_range': (
                        f'{get_column_letter(first_col)}{row_index}:'
                        f'{get_column_letter(last_col)}{row_index}'
                    ),
                    'source_values': values,
                    'normalized_values': {},
                })
                if len(rows) > MAX_WORKBOOK_ROWS:
                    raise WorkbookImportError('workbook_too_many_rows')
    except WorkbookImportError:
        raise
    except Exception as exc:
        raise WorkbookImportError('invalid_xlsx') from exc
    finally:
        workbook.close()

    if not rows:
        raise WorkbookImportError('workbook_has_no_populated_rows')

    return rows


def normalize_workbook_rows(rows, source_kind):
    """Add conservative, header-based field hints while preserving source cells."""
    by_sheet = {}
    for row in rows:
        by_sheet.setdefault(row['source_sheet'], []).append(row)

    for sheet_rows in by_sheet.values():
        sheet_rows.sort(key=lambda row: row['source_row'])
        header_row = sheet_rows[0]
        labels = {
            column: cell.get('value')
            for column, cell in header_row['source_values'].items()
            if isinstance(cell.get('value'), str) and cell['value'].strip()
        }
        if any(
            label in {'售后状态', '故障原因具体描述', '售后出库', '售后入库'}
            for label in labels.values()
        ):
            profile = 'service_history'
        elif any(
            label
            in {
                '出库产品',
                '流程编号',
                '状态（已出库/未出库）',  # noqa: RUF001 - exact source header
            }
            for label in labels.values()
        ):
            profile = 'shipment_history'
        else:
            profile = source_kind
        header_map = IMPORT_HEADERS.get(profile, {})
        candidates = {
            column: header_map[label.strip()]
            for column, label in labels.items()
            if label.strip() in header_map
        }
        target_counts = {}
        for target in candidates.values():
            target_counts[target] = target_counts.get(target, 0) + 1
        ambiguous = sorted(
            target for target, count in target_counts.items() if count > 1
        )
        column_targets = {
            column: target
            for column, target in candidates.items()
            if target_counts[target] == 1
        }

        if len(column_targets) < 2:
            for row in sheet_rows:
                row['normalized_values'] = {
                    'mapping_status': 'unrecognized_header',
                    'mapping_profile': profile,
                }
            continue

        header_row['normalized_values'] = {
            'row_type': 'header',
            'mapping_status': 'recognized',
            'mapping_profile': profile,
            'column_targets': column_targets,
            'ambiguous_fields': ambiguous,
        }
        for row in sheet_rows[1:]:
            unmapped_columns = sorted(
                column
                for column, cell in row['source_values'].items()
                if column not in column_targets and cell['value'] is not None
            )
            fields = {
                target: row['source_values'][column]['value']
                for column, target in column_targets.items()
                if row['source_values'][column]['value'] is not None
            }
            row['normalized_values'] = {
                'row_type': 'data',
                'mapping_status': (
                    'partial' if ambiguous or unmapped_columns else 'mapped'
                ),
                'mapping_profile': profile,
                'fields': fields,
                'unmapped_columns': unmapped_columns,
                'ambiguous_fields': ambiguous,
            }

    return rows
