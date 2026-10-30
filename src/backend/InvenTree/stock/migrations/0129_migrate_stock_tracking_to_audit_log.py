"""Copy legacy stock tracking entries (StockItemTracking) into the audit log (AuditLogEntry).

Each StockItemTracking row is converted to a single AuditLogEntry:

- The entry is recorded against the stock item (even if the item has since been deleted)
- The parent reference is the part (so the entry is included in the history of the part)
- The tracking type is recorded as the event type (StockHistoryCode values are unchanged)
  - 'EDITED' entries are recorded as regular updates (no event type)
  - Entries which record the creation of a stock item are recorded as CREATE entries
- The user, date and notes are copied across
- Tracking deltas are converted to audit log changes / deltas:
  - Status changes are recorded as field changes ('status' / 'status_custom_key')
  - Location changes (with a known previous location) are recorded as field changes
  - For CREATE entries, initial field values are recorded as field changes
  - References to other objects (by pk) are recorded as {model_type, pk, str} references
  - Any other deltas are copied as-is
- The pk of the original tracking entry is retained in additional_data['tracking_id']

The legacy StockItemTracking rows are not modified (or deleted) by this migration.
"""

from decimal import Decimal, InvalidOperation

from django.db import migrations

# StockHistoryCode values (copied here, as migrations should not import application code)
CREATED = 1
EDITED = 5
SPLIT_FROM_PARENT = 40
CREATED_FROM_DISASSEMBLY = 47
BUILD_OUTPUT_CREATED = 50
RECEIVED_AGAINST_PURCHASE_ORDER = 70

# Tracking codes which record the creation of a stock item
CREATE_CODES = {
    CREATED,
    SPLIT_FROM_PARENT,
    CREATED_FROM_DISASSEMBLY,
    BUILD_OUTPUT_CREATED,
    RECEIVED_AGAINST_PURCHASE_ORDER,
}

# AuditLogEntry action codes (as defined by django-auditlog)
ACTION_CREATE = 0
ACTION_UPDATE = 1

# Delta keys which reference other objects (by pk)
REFERENCE_KEYS = {
    'stockitem': ('stock', 'stockitem'),
    'location': ('stock', 'stocklocation'),
    'old_location': ('stock', 'stocklocation'),
    'stockitemlocation': ('stock', 'stocklocation'),
    'part': ('part', 'part'),
    'customer': ('company', 'company'),
    'buildorder': ('build', 'build'),
    'build_order': ('build', 'build'),
    'purchaseorder': ('order', 'purchaseorder'),
    'salesorder': ('order', 'salesorder'),
    'returnorder': ('order', 'returnorder'),
    'transferorder': ('order', 'transferorder'),
}

# Delta keys which are recorded as field changes (rather than deltas)
STATUS_KEYS = ('status', 'status_logical', 'old_status', 'old_status_logical')

# For CREATE entries, these deltas record the initial value of the stock item field
CREATE_FIELD_KEYS = ('quantity', 'location', 'serial', 'batch')

BATCH_SIZE = 1000


def format_quantity(quantity) -> str:
    """Format a stock quantity for display (e.g. '10', '2.5')."""
    try:
        value = Decimal(str(quantity)).normalize()
    except (InvalidOperation, TypeError, ValueError):
        return str(quantity)

    # Remove exponent notation (e.g. 1E+1)
    return format(value, 'f')


def stock_item_str(item) -> str:
    """Return a string representation of a stock item.

    Note: This approximates StockItem.__str__ - historical models do not provide model
    methods, and the configurable part name format cannot be applied here.
    """
    if item.serial:
        return f'{item.part.name} #{item.serial}'

    return f'{format_quantity(item.quantity)} x {item.part.name}'


def reference_str(model_type: str, instance) -> str:
    """Return a string representation for a referenced object."""
    if model_type == 'stock.stockitem':
        return stock_item_str(instance)

    if model_type == 'stock.stocklocation':
        return instance.pathstring or instance.name

    if model_type in (
        'build.build',
        'order.purchaseorder',
        'order.salesorder',
        'order.returnorder',
        'order.transferorder',
    ):
        return instance.reference

    return instance.name


def to_pk(value):
    """Convert a delta value to a primary key (or None)."""
    if value is None or isinstance(value, bool):
        return None

    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def convert_entry(entry, references: dict) -> dict:
    """Convert a single StockItemTracking entry into AuditLogEntry field values."""
    code = entry.tracking_type
    deltas = dict(entry.deltas or {}) if isinstance(entry.deltas, dict) else {}

    action = ACTION_CREATE if code in CREATE_CODES else ACTION_UPDATE

    changes = {}

    # Status changes are recorded as field changes
    if 'status' in deltas or 'status_logical' in deltas:
        new_status = deltas.get('status')
        new_logical = deltas.get('status_logical', new_status)
        old_status = deltas.get('old_status')
        old_logical = deltas.get('old_status_logical', old_status)

        changes['status'] = [old_logical, new_logical]

        # A custom status is recorded separately to the logical status
        new_custom = new_status if new_status != new_logical else None
        old_custom = old_status if old_status != old_logical else None

        if new_custom is not None or old_custom is not None:
            changes['status_custom_key'] = [old_custom, new_custom]

    for key in STATUS_KEYS:
        deltas.pop(key, None)

    # A location change (with known previous location) is recorded as a field change
    if 'old_location' in deltas:
        old_location = to_pk(deltas.pop('old_location'))
        new_location = to_pk(deltas.pop('location', None))

        if old_location != new_location:
            changes['location'] = [old_location, new_location]

    # The initial values of a new stock item are recorded as field changes
    if action == ACTION_CREATE:
        for key in CREATE_FIELD_KEYS:
            if key in deltas:
                value = deltas.pop(key)

                if key == 'location':
                    value = to_pk(value)
                elif key == 'quantity':
                    value = format_quantity(value)
                elif value is not None:
                    value = str(value)

                if value is not None:
                    changes[key] = [None, value]

    # The customer name is recorded as the string representation of the customer reference
    customer_name = deltas.pop('customer_name', None)

    # Convert references (by pk) to {model_type, pk, str}
    for key, (app_label, model_name) in REFERENCE_KEYS.items():
        if key not in deltas:
            continue

        pk = to_pk(deltas[key])

        if pk is None:
            continue

        model_type = f'{app_label}.{model_name}'
        instance = references.get(model_type, {}).get(pk)

        if instance is not None:
            text = reference_str(model_type, instance)
        elif key == 'customer' and customer_name:
            text = customer_name
        else:
            # The referenced object no longer exists
            text = None

        deltas[key] = {'model_type': model_type, 'pk': pk, 'str': text}

    additional_data = {'tracking_id': entry.pk}

    if deltas:
        additional_data['deltas'] = deltas

    item = entry.item

    if item is not None:
        object_repr = stock_item_str(item)
    elif entry.part is not None:
        object_repr = entry.part.name
    else:
        object_repr = ''

    user = entry.user

    return {
        'object_pk': str(entry.item_id) if entry.item_id is not None else '',
        'object_id': entry.item_id,
        'object_repr': object_repr,
        'action': action,
        'changes': changes,
        'changes_text': '',
        'timestamp': entry.date,
        'actor_id': entry.user_id,
        'actor_email': getattr(user, 'email', None) or None,
        'actor_username': getattr(user, 'username', None),
        'parent_object_pk': str(entry.part_id) if entry.part_id is not None else None,
        'event_type': None if code == EDITED else code,
        'notes': entry.notes[:512] if entry.notes else None,
        'additional_data': additional_data,
    }


def collect_references(apps, entries) -> dict:
    """Fetch all objects referenced (by pk) in the deltas of the provided entries."""
    required = {}

    for entry in entries:
        if not isinstance(entry.deltas, dict):
            continue

        for key, (app_label, model_name) in REFERENCE_KEYS.items():
            if (pk := to_pk(entry.deltas.get(key))) is not None:
                required.setdefault(f'{app_label}.{model_name}', set()).add(pk)

    references = {}

    for model_type, pks in required.items():
        app_label, model_name = model_type.split('.')
        model = apps.get_model(app_label, model_name)

        queryset = model.objects.all()

        if model_type == 'stock.stockitem':
            queryset = queryset.select_related('part')

        references[model_type] = queryset.in_bulk(list(pks))

    return references


def migrate_tracking_entries(apps, schema_editor):
    """Copy all StockItemTracking entries into the audit log."""
    StockItemTracking = apps.get_model('stock', 'stockitemtracking')
    AuditLogEntry = apps.get_model('audit', 'auditlogentry')
    ContentType = apps.get_model('contenttypes', 'contenttype')

    n = StockItemTracking.objects.count()

    if n == 0:
        return

    print(f'\nstock.migrations.0129: Migrating {n} stock tracking entries to the audit log')

    stock_ct, _ = ContentType.objects.get_or_create(
        app_label='stock', model='stockitem'
    )
    part_ct, _ = ContentType.objects.get_or_create(app_label='part', model='part')

    queryset = StockItemTracking.objects.select_related(
        'item', 'item__part', 'part', 'user'
    ).order_by('pk')

    last_pk = 0
    migrated = 0

    while True:
        entries = list(queryset.filter(pk__gt=last_pk)[:BATCH_SIZE])

        if not entries:
            break

        references = collect_references(apps, entries)

        audit_entries = []

        for entry in entries:
            data = convert_entry(entry, references)

            audit_entries.append(
                AuditLogEntry(
                    content_type_id=stock_ct.pk,
                    parent_content_type_id=part_ct.pk
                    if data['parent_object_pk'] is not None
                    else None,
                    **data,
                )
            )

        AuditLogEntry.objects.bulk_create(audit_entries, batch_size=BATCH_SIZE)

        migrated += len(audit_entries)
        last_pk = entries[-1].pk


class Migration(migrations.Migration):
    """Copy legacy stock tracking entries into the audit log."""

    dependencies = [
        ('stock', '0128_remove_stockitem_notes'),
        ('audit', '0003_event_type'),
        ('build', '0060_remove_build_notes'),
        ('company', '0083_company_is_internal'),
        ('order', '0124_purchaseorder_delivery_address'),
        ('part', '0155_move_pricing_models'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        # The migrated entries are retained on reversal, as the legacy table
        # (dropped in the following migration) cannot be restored
        migrations.RunPython(
            migrate_tracking_entries, reverse_code=migrations.RunPython.noop
        )
    ]
