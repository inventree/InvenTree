"""Migration coverage for adding a format to existing notes."""

from django.test import tag

from django_test_migrations.contrib.unittest_case import MigratorTestCase


@tag('migration_test')
class NoteContentTypeMigrationTests(MigratorTestCase):
    """Existing HTML notes and templates retain their content and image links."""

    migrate_from = ('common', '0052_remove_notesimage_model_id_and_more')
    migrate_to = ('common', '0053_note_content_type')

    def prepare(self):
        """Populate the historical model before the format field exists."""
        Note = self.old_state.apps.get_model('common', 'Note')
        ContentType = self.old_state.apps.get_model('contenttypes', 'ContentType')
        NotesImage = self.old_state.apps.get_model('common', 'NotesImage')
        content_type, _ = ContentType.objects.get_or_create(
            app_label='part', model='part'
        )
        self.content = ' <p>Existing HTML &amp; image</p>\n'
        self.note_pk = Note.objects.create(
            title='Existing note',
            content=self.content,
            primary=True,
            model_type=content_type,
            model_id=1,
        ).pk
        self.template_pk = Note.objects.create(
            title='Existing template', content=self.content, template=True
        ).pk
        self.image_pk = NotesImage.objects.create(
            note_id=self.note_pk, image='notes/existing.png'
        ).pk

    def test_existing_content_is_unchanged(self):
        """Only the new format field changes during this migration."""
        Note = self.new_state.apps.get_model('common', 'Note')
        NotesImage = self.new_state.apps.get_model('common', 'NotesImage')
        for pk in [self.note_pk, self.template_pk]:
            item = Note.objects.get(pk=pk)
            self.assertEqual(item.content_type, 'text/html')
            self.assertEqual(item.content, self.content)
        self.assertTrue(Note.objects.get(pk=self.note_pk).primary)
        self.assertTrue(Note.objects.get(pk=self.template_pk).template)
        image = NotesImage.objects.get(pk=self.image_pk)
        self.assertEqual(image.note_id, self.note_pk)
        self.assertEqual(image.image.name, 'notes/existing.png')
