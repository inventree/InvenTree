# Generated manually for RepairOrder feature

import InvenTree.fields
import InvenTree.models
import django.core.validators
import django.db.models.deletion
import generic.states.fields
import generic.states.states
import generic.states.transition
import generic.states.validators
import order.status_codes
import order.validators
import taggit.managers
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('common', '0046_alter_emailmessage_global_id_and_more'),
        ('company', '0080_company_tags'),
        ('order', '0120_purchaseorder_tags_returnorder_tags_salesorder_tags_and_more'),
        ('part', '0151_part_consumable'),
        ('stock', '0123_remove_stockitem_review_needed'),
        ('taggit', '0006_rename_taggeditem_content_type_object_id_taggit_tagg_content_8fc721_idx'),
        ('users', '0015_alter_userprofile_type'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='RepairOrder',
            fields=[
                ('metadata', models.JSONField(blank=True, help_text='JSON metadata field, for use by external plugins', null=True, verbose_name='Plugin Metadata')),
                ('reference_int', models.BigIntegerField(default=0)),
                ('notes', InvenTree.fields.InvenTreeNotesField(blank=True, help_text='Markdown notes (optional)', max_length=50000, null=True, verbose_name='Notes')),
                ('barcode_data', models.CharField(blank=True, help_text='Third party barcode data', max_length=500, verbose_name='Barcode Data')),
                ('barcode_hash', models.CharField(blank=True, help_text='Unique hash of barcode data', max_length=128, verbose_name='Barcode Hash')),
                ('description', models.CharField(blank=True, help_text='Order description (optional)', max_length=250, verbose_name='Description')),
                ('link', InvenTree.fields.InvenTreeURLField(blank=True, help_text='Link to external page', max_length=2000, verbose_name='Link')),
                ('start_date', models.DateField(blank=True, help_text='Scheduled start date for this order', null=True, verbose_name='Start date')),
                ('target_date', models.DateField(blank=True, help_text='Expected date for order delivery. Order will be overdue after this date.', null=True, verbose_name='Target Date')),
                ('creation_date', models.DateField(blank=True, null=True, verbose_name='Creation Date')),
                ('issue_date', models.DateField(blank=True, help_text='Date order was issued', null=True, verbose_name='Issue Date')),
                ('updated_at', models.DateTimeField(blank=True, help_text='Timestamp of last update', null=True, verbose_name='Updated At')),
                ('reference', models.CharField(default=order.validators.generate_next_repair_order_reference, help_text='Repair Order reference', max_length=64, unique=True, validators=[order.validators.validate_repair_order_reference], verbose_name='Reference')),
                ('serial', models.CharField(blank=True, help_text='Serial number for the item being repaired', max_length=100, verbose_name='Serial Number')),
                ('status', generic.states.fields.InvenTreeCustomStatusModelField(choices=[(10, 'Pending'), (20, 'In Progress'), (25, 'On Hold'), (30, 'Complete'), (40, 'Cancelled')], default=10, help_text='Repair order status', validators=[generic.states.validators.CustomStatusCodeValidator(status_class=order.status_codes.RepairOrderStatus)], verbose_name='Status')),
                ('customer_reference', models.CharField(blank=True, help_text='Customer order reference code', max_length=64, verbose_name='Customer Reference')),
                ('complete_date', models.DateField(blank=True, help_text='Date order was completed', null=True, verbose_name='Completion Date')),
                ('address', models.ForeignKey(blank=True, help_text='Company address for this order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='company.address', verbose_name='Address')),
                ('contact', models.ForeignKey(blank=True, help_text='Point of contact for this order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='company.contact', verbose_name='Contact')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Created By')),
                ('customer', models.ForeignKey(help_text='Company for which repair work is performed', limit_choices_to={'is_customer': True}, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='company.company', verbose_name='Customer')),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item', models.ForeignKey(blank=True, help_text='Stock item being repaired', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='stock.stockitem', verbose_name='Stock Item')),
                ('part', models.ForeignKey(blank=True, help_text='Part being repaired', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='part.part', verbose_name='Part')),
                ('project_code', models.ForeignKey(blank=True, help_text='Project code for this order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='common.projectcode', verbose_name='Project Code')),
                ('responsible', models.ForeignKey(blank=True, help_text='User responsible for this order', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='users.owner', verbose_name='Responsible')),
            ],
            options={
                'verbose_name': 'Repair Order',
            },
        ),
        migrations.CreateModel(
            name='RepairOrderLine',
            fields=[
                ('metadata', models.JSONField(blank=True, help_text='JSON metadata field, for use by external plugins', null=True, verbose_name='Plugin Metadata')),
                ('reference', models.CharField(blank=True, help_text='Line item reference', max_length=100, verbose_name='Reference')),
                ('line_int', models.BigIntegerField(default=0)),
                ('notes', models.TextField(blank=True, help_text='Line item notes', verbose_name='Notes')),
                ('link', InvenTree.fields.InvenTreeURLField(blank=True, help_text='Link to external information', max_length=2000, verbose_name='Link')),
                ('target_date', models.DateField(blank=True, help_text='Expected date for delivery of this line item', null=True, verbose_name='Target Date')),
                ('consumed_date', models.DateField(blank=True, help_text='The date this repair line item was consumed', null=True, verbose_name='Consumed Date')),
                ('quantity', models.DecimalField(decimal_places=5, default=1, help_text='Quantity required for repair', max_digits=15, validators=[django.core.validators.MinValueValidator(0)], verbose_name='Quantity')),
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order', models.ForeignKey(help_text='Repair Order', on_delete=django.db.models.deletion.CASCADE, related_name='lines', to='order.repairorder', verbose_name='Order')),
                ('part', models.ForeignKey(blank=True, help_text='Part required for repair', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_order_lines', to='part.part', verbose_name='Part')),
                ('stock_item', models.ForeignKey(blank=True, help_text='Stock item required for repair', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_order_lines', to='stock.stockitem', verbose_name='Stock Item')),
                ('project_code', models.ForeignKey(blank=True, help_text='Project code for this line item', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_order_lines', to='common.projectcode', verbose_name='Project Code')),
            ],
            options={
                'verbose_name': 'Repair Order Line Item',
            },
        ),
    ]