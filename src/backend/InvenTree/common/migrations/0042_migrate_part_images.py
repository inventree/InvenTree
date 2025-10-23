

import hashlib

from pathlib import Path
from django.db import migrations
from django.core.files.base import ContentFile


def forwards_migrate_part_images(apps, schema_editor):
    """
    Perform the forward migration of Part.image → InvenTreeImage.

    Deduplication strategy:
      - Compute SHA-256 hash of each file's raw bytes.
      - Maintain a dict mapping hash → saved storage filename.
      - On first encounter of a hash, save the file and record its storage path.
      - On subsequent encounters, reuse the recorded storage path.

    This ensures that identical image files (even if they had different
    original filenames or paths) are only stored once in the backend.
    """

    Part = apps.get_model('part', 'Part')
    InvenTreeImage = apps.get_model('common', 'InvenTreeImage')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    part_ct = ContentType.objects.get_for_model(Part)

    # A mapping from hash → stored filename in the ImageField storage
    saved_files = {}

    for part in Part.objects.exclude(image__isnull=True).exclude(image=''):
        # Open and read the image bytes
        try:
            with part.image.open('rb') as f:
                data = f.read()
        except IOError:
            # if file missing or unreadable, skip
            continue

        # Compute a hash of the file contents
        file_hash = hashlib.sha256(data).hexdigest()

        if file_hash not in saved_files:
            original_name = Path(part.image.name).name
            storage = InvenTreeImage._meta.get_field('image').storage
            stored_name = storage.get_available_name(original_name)

            img = InvenTreeImage(
                content_type_id=part_ct.id,
                object_id=part.pk,
                primary=True,
            )
            img.image.save(stored_name, ContentFile(data), save=True)

            saved_files[file_hash] = img.image.name

        else:
            stored_name = saved_files[file_hash]

            img = InvenTreeImage(
                content_type_id=part_ct.id,
                object_id=part.pk,
                primary=True,
            )
            img.image.name = stored_name
            img.save()


def reverse_migrate_inventree_images_to_part(apps, schema_editor):
    """Reverse migration: move InvenTreeImage back to Part.image."""
    Part = apps.get_model('part', 'Part')
    InvenTreeImage = apps.get_model('common', 'InvenTreeImage')
    ContentType = apps.get_model('contenttypes', 'ContentType')

    part_ct = ContentType.objects.get_for_model(Part)
    for img in InvenTreeImage.objects.filter(content_type=part_ct, primary=True):
        try:
            part = Part.objects.get(pk=img.object_id)
            part.image = img.image
            part.save()
            print(f"Restored image for part: {part.name} (ID: {part.pk})")
        except Part.DoesNotExist:
            print(f"Part with ID {img.object_id} not found, skipping...")


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0139_remove_bomitem_overage'),
        ('common', '0041_migrate_company_images'),
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.RunPython(
            forwards_migrate_part_images,
            reverse_migrate_inventree_images_to_part,
        ),
    ]
