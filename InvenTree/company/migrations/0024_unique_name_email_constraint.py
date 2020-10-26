from django.db import migrations, models


def make_empty_email_field_null(apps, schema_editor):
    Company = apps.get_model('company', 'Company')
    for company in Company.objects.all():
        if company.email == '':
            company.email = None
            company.save()


class Migration(migrations.Migration):

    dependencies = [
        ('company', '0023_auto_20200808_0715'),
    ]

    operations = [
        # Allow email field to be NULL
        migrations.AlterField(
            model_name='company',
            name='email',
            field=models.EmailField(blank=True, help_text='Contact email address', max_length=254, null=True, unique=False, verbose_name='Email'),
        ),
        # Convert empty email string to NULL
        migrations.RunPython(make_empty_email_field_null),
        # Remove unique constraint on name field
        migrations.AlterField(
            model_name='company',
            name='name',
            field=models.CharField(help_text='Company name', max_length=100, verbose_name='Company name'),
        ),
        # Add unique constraint on name/email pair
        migrations.AddConstraint(
            model_name='company',
            constraint=models.UniqueConstraint(fields=('name', 'email'), name='unique_name_email_pair'),
        ),
    ]
