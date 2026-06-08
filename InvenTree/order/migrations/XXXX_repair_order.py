# Generated migration for RepairOrder model
# InvenTree/order/migrations/XXXX_repair_order.py

from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import InvenTree.fields
import InvenTree.models


class Migration(migrations.Migration):
    """Create repair_order table and related fields for RepairOrder model.

    This migration introduces a new order type (RepairOrder) that extends
    the existing order management system. It tracks repair work on customer
    units, including parts used, labor, and descriptions.
    """

    dependencies = [
        ('order', 'XXXX_previous_migration'),  # Replace with actual previous migration
        ('stock', 'XXXX_stock_migration'),      # Replace with actual stock migration
        ('company', 'XXXX_company_migration'),  # Replace with actual company migration
        ('part', 'XXXX_part_migration'),        # Replace with actual part migration
    ]

    operations = [
        # Create the repair_order table
        migrations.CreateModel(
            name='RepairOrder',
            fields=[
                # Base Order fields (inherited from Order model)
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('order_id', models.CharField(max_length=64, unique=True, verbose_name='Order ID')),
                ('description', models.CharField(blank=True, max_length=250, verbose_name='Description')),
                ('creation_date', models.DateField(auto_now_add=True, verbose_name='Creation Date')),
                ('target_date', models.DateField(blank=True, null=True, verbose_name='Target Date')),
                ('complete_date', models.DateField(blank=True, null=True, verbose_name='Completion Date')),
                ('status', models.PositiveIntegerField(choices=[
                    (10, 'Pending'),
                    (20, 'In Progress'),
                    (30, 'Completed'),
                    (40, 'Cancelled'),
                ], default=10, verbose_name='Status')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('link', models.URLField(blank=True, verbose_name='External Link')),
                ('responsible', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders_responsible', to='auth.user', verbose_name='Responsible')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders_created', to='auth.user', verbose_name='Created By')),

                # RepairOrder-specific fields
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repair_orders', to='company.company', verbose_name='Customer')),
                ('customer_unit', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_orders', to='stock.stockitem', verbose_name='Customer Unit')),
                ('job_description', models.TextField(blank=True, verbose_name='Job Description')),
                ('symptoms', models.TextField(blank=True, verbose_name='Reported Symptoms')),
                ('diagnosis', models.TextField(blank=True, verbose_name='Diagnosis')),
                ('resolution', models.TextField(blank=True, verbose_name='Resolution')),
                ('labor_hours', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Labor Hours')),
                ('labor_rate', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True, verbose_name='Labor Rate')),
                ('labor_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Labor Cost')),
                ('parts_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Parts Cost')),
                ('total_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Total Cost')),
                ('warranty', models.BooleanField(default=False, verbose_name='Under Warranty')),
                ('serial_number', models.CharField(blank=True, max_length=100, verbose_name='Serial Number')),
                ('received_date', models.DateField(blank=True, null=True, verbose_name='Date Received')),
                ('start_date', models.DateField(blank=True, null=True, verbose_name='Work Start Date')),
                ('shipped_date', models.DateField(blank=True, null=True, verbose_name='Date Shipped')),
                ('tracking_number', models.CharField(blank=True, max_length=100, verbose_name='Tracking Number')),
                ('carrier', models.CharField(blank=True, max_length=100, verbose_name='Carrier')),
                ('invoice_number', models.CharField(blank=True, max_length=100, verbose_name='Invoice Number')),
                ('invoice_date', models.DateField(blank=True, null=True, verbose_name='Invoice Date')),
                ('invoice_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Invoice Amount')),
                ('paid_date', models.DateField(blank=True, null=True, verbose_name='Date Paid')),
                ('paid_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Amount Paid')),
                ('payment_method', models.CharField(blank=True, max_length=50, verbose_name='Payment Method')),
                ('payment_reference', models.CharField(blank=True, max_length=100, verbose_name='Payment Reference')),
                ('payment_notes', models.TextField(blank=True, verbose_name='Payment Notes')),
                ('customer_contact', models.CharField(blank=True, max_length=100, verbose_name='Customer Contact')),
                ('customer_email', models.EmailField(blank=True, max_length=254, verbose_name='Customer Email')),
                ('customer_phone', models.CharField(blank=True, max_length=20, verbose_name='Customer Phone')),
                ('customer_address', models.TextField(blank=True, verbose_name='Customer Address')),
                ('shipping_address', models.TextField(blank=True, verbose_name='Shipping Address')),
                ('billing_address', models.TextField(blank=True, verbose_name='Billing Address')),
                ('shipping_method', models.CharField(blank=True, max_length=100, verbose_name='Shipping Method')),
                ('shipping_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Shipping Cost')),
                ('insurance_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Insurance Cost')),
                ('handling_cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Handling Cost')),
                ('tax_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Tax Amount')),
                ('discount_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Discount Amount')),
                ('deposit_amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Deposit Amount')),
                ('deposit_date', models.DateField(blank=True, null=True, verbose_name='Deposit Date')),
                ('deposit_reference', models.CharField(blank=True, max_length=100, verbose_name='Deposit Reference')),
                ('balance_due', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Balance Due')),
                ('balance_due_date', models.DateField(blank=True, null=True, verbose_name='Balance Due Date')),
                ('terms_accepted', models.BooleanField(default=False, verbose_name='Terms Accepted')),
                ('terms_accepted_date', models.DateField(blank=True, null=True, verbose_name='Terms Accepted Date')),
                ('terms_accepted_by', models.CharField(blank=True, max_length=100, verbose_name='Terms Accepted By')),
                ('customer_signature', models.TextField(blank=True, verbose_name='Customer Signature')),
                ('technician_signature', models.TextField(blank=True, verbose_name='Technician Signature')),
                ('internal_notes', models.TextField(blank=True, verbose_name='Internal Notes')),
                ('customer_notes', models.TextField(blank=True, verbose_name='Customer Notes')),
                ('is_archived', models.BooleanField(default=False, verbose_name='Archived')),
                ('archived_date', models.DateField(blank=True, null=True, verbose_name='Archived Date')),
                ('archived_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='archived_repair_orders', to='auth.user', verbose_name='Archived By')),
            ],
            options={
                'verbose_name': 'Repair Order',
                'verbose_name_plural': 'Repair Orders',
                'db_table': 'order_repairorder',
                'ordering': ['-creation_date', '-id'],
                'permissions': [
                    ('view_repairorder', 'Can view repair order'),
                    ('add_repairorder', 'Can add repair order'),
                    ('change_repairorder', 'Can change repair order'),
                    ('delete_repairorder', 'Can delete repair order'),
                    ('approve_repairorder', 'Can approve repair order'),
                    ('complete_repairorder', 'Can complete repair order'),
                    ('cancel_repairorder', 'Can cancel repair order'),
                    ('archive_repairorder', 'Can archive repair order'),
                ],
            },
            bases=(InvenTree.models.InvenTreeModel, models.Model),
        ),

        # Create the repair_order_item table for tracking parts used
        migrations.CreateModel(
            name='RepairOrderItem',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.DecimalField(decimal_places=2, default=1, max_digits=10, verbose_name='Quantity')),
                ('unit_price', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True, verbose_name='Unit Price')),
                ('total_price', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Total Price')),
                ('notes', models.CharField(blank=True, max_length=250, verbose_name='Notes')),
                ('reference', models.CharField(blank=True, max_length=100, verbose_name='Reference')),
                ('is_billed', models.BooleanField(default=True, verbose_name='Billed to Customer')),
                ('is_warranty', models.BooleanField(default=False, verbose_name='Warranty Replacement')),
                ('is_free', models.BooleanField(default=False, verbose_name='Free of Charge')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='items', to='order.repairorder', verbose_name='Repair Order')),
                ('part', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='repair_order_items', to='part.part', verbose_name='Part')),
                ('stock_item', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='repair_order_items', to='stock.stockitem', verbose_name='Stock Item')),
            ],
            options={
                'verbose_name': 'Repair Order Item',
                'verbose_name_plural': 'Repair Order Items',
                'db_table': 'order_repairorderitem',
                'ordering': ['order', 'id'],
            },
            bases=(InvenTree.models.InvenTreeModel, models.Model),
        ),

        # Create the repair_order_labor table for tracking labor entries
        migrations.CreateModel(
            name='RepairOrderLabor',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('description', models.CharField(max_length=250, verbose_name='Description')),
                ('hours', models.DecimalField(decimal_places=2, max_digits=10, verbose_name='Hours')),
                ('rate', models.DecimalField(blank=True, decimal_places=4, max_digits=10, null=True, verbose_name='Rate')),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='Cost')),
                ('date', models.DateField(default=django.utils.timezone.now, verbose_name='Date')),
                ('technician', models.CharField(blank=True, max_length=100, verbose_name='Technician')),
                ('notes', models.TextField(blank=True, verbose_name='Notes')),
                ('is_billed', models.BooleanField(default=True, verbose_name='Billed to Customer')),
                ('is_warranty', models.BooleanField(default=False, verbose_name='Warranty Labor')),
                ('order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='labor_entries', to='order.repairorder', verbose_name='Repair Order')),
            ],
            options={
                'verbose_name': 'Repair Order Labor',
                'verbose_name_plural': 'Repair Order Labor Entries',
                'db_table': 'order_repairorderlabor',
                'ordering': ['order', 'date', 'id'],
            },
            bases=(InvenTree.models.InvenTreeModel, models.Model),
        ),

        # Add indexes for performance
        migrations.AddIndex(
            model_name='repairorder',
            index=models.Index(fields=['status', 'creation_date'], name='order_repair_status_date_idx'),
        ),
        migrations.AddIndex(
            model_name='repairorder',
            index=models.Index(fields=['customer', 'status'], name='order_repair_customer_status_idx'),
        ),
        migrations.AddIndex(
            model_name='repairorder',
            index=models.Index(fields=['customer_unit'], name='order_repair_unit_idx'),
        ),
        migrations.AddIndex(
            model_name='repairorderitem',
            index=models.Index(fields=['order', 'part'], name='order_repair_item_order_part_idx'),
        ),
        migrations.AddIndex(
            model_name='repairorderlabor',
            index=models.Index(fields=['order', 'date'], name='order_repair_labor_order_date_idx'),
        ),
    ]