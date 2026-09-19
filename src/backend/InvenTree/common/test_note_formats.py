"""Regression tests for typed note source preservation and format boundaries."""

import io
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.urls import reverse

from PIL import Image

from common.models import Note, NotesImage
from common.notes import NoteContentType
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part
from report.templatetags.report import note as render_note


class TypedNoteTests(InvenTreeAPITestCase):
    """Test note formats across API, model, duplication, and report paths."""

    def setUp(self):
        """Create a note owner with change permission."""
        super().setUp()
        self.assignRole('part.change')
        self.part = Part.objects.create(name='Typed note part')
        self.url = reverse('api-note-list')

    def create_note(self, content_type, content, **kwargs):
        """Create a note through its production serializer."""
        return self.post(
            self.url,
            {
                'model_type': 'part',
                'model_id': self.part.pk,
                'title': 'Typed note',
                'content_type': content_type,
                'content': content,
                **kwargs,
            },
            expected_code=201,
        ).data

    def test_raw_content_round_trip(self):
        """Raw formats survive API and model writes without any normalization."""
        vectors = [
            (
                NoteContentType.JSON,
                ' \n{"n":9007199254740993,"e":1.200e+30,"escaped":"\\u010d","html":"<device>&</device>"}\n\t',
            ),
            (NoteContentType.JSON, ' null\n'),
            (NoteContentType.JSON, '[true, false, "**text**"]'),
            (
                NoteContentType.PLAIN_TEXT,
                '\n # Heading\n\n<device>literal</device>\n\t',
            ),
            (NoteContentType.PLAIN_TEXT, ''),
        ]
        for content_type, content in vectors:
            with self.subTest(content_type=content_type, content=content):
                data = self.create_note(content_type, content)
                self.assertEqual(data['content'], content)
                self.assertEqual(data['content_type'], content_type)
                item = Note.objects.get(pk=data['pk'])
                self.assertEqual(item.content, content)
                item.save()
                item.refresh_from_db()
                self.assertEqual(item.content, content)
                url = reverse('api-note-detail', kwargs={'pk': item.pk})
                self.assertEqual(self.get(url).data['content'], content)
                updated = '\n' + content if content else '\n'
                self.patch(url, {'content': updated}, expected_code=200)
                self.assertEqual(self.get(url).data['content'], updated)

    def test_json_rejection_preserves_saved_content(self):
        """Invalid edits fail explicitly without replacing a valid source."""
        data = self.create_note(NoteContentType.JSON, '{}')
        url = reverse('api-note-detail', kwargs={'pk': data['pk']})
        for content in ['', ' ', '{', 'NaN', 'Infinity', '-Infinity', '{"x":NaN}']:
            with self.subTest(content=content):
                response = self.patch(url, {'content': content}, expected_code=400)
                self.assertIn('content', response.data)
                self.assertEqual(self.get(url).data['content'], '{}')

    def test_json_recursion_limit_is_a_validation_error(self):
        """Parser recursion errors reject creation and edits without changing data."""
        data = self.create_note(NoteContentType.JSON, '{}')
        url = reverse('api-note-detail', kwargs={'pk': data['pk']})

        # Replace only the note parser reference, leaving request JSON decoding intact.
        with patch('common.notes.json') as note_json:
            note_json.loads.side_effect = RecursionError('JSON recursion limit')
            response = self.post(
                self.url,
                {
                    'model_type': 'part',
                    'model_id': self.part.pk,
                    'title': 'Deep JSON',
                    'content_type': NoteContentType.JSON,
                    'content': '[]',
                },
                expected_code=400,
            )
            self.assertEqual(response.data['content'], ['JSON is nested too deeply.'])
            self.assertFalse(Note.objects.filter(title='Deep JSON').exists())

            response = self.patch(url, {'content': '[]'}, expected_code=400)
            self.assertEqual(response.data['content'], ['JSON is nested too deeply.'])

        self.assertEqual(self.get(url).data['content'], '{}')

    def test_unknown_types_rejected(self):
        """Unsupported, empty, and null content types are rejected."""
        for content_type in ['text/unknown', 'text/markdown', '', None]:
            response = self.post(
                self.url,
                {
                    'title': 'Unknown',
                    'model_type': 'part',
                    'model_id': self.part.pk,
                    'content_type': content_type,
                    'content': '{}',
                },
                expected_code=400,
            )
            self.assertIn('content_type', response.data)

    def test_model_rejects_unknown_format(self):
        """Direct model creation rejects unsupported formats without saving a note."""
        with self.assertRaises(ValidationError) as error:
            Note.objects.create(
                model_type=self.part.get_content_type(),
                model_id=self.part.pk,
                title='Unsupported format',
                content_type='text/unknown',
                content='<p>Source</p>',
            )
        self.assertIn('content_type', error.exception.message_dict)
        self.assertFalse(self.part.notes_list.exists())

    def test_content_type_is_permanent(self):
        """Notes and templates reject every format transition, with or without content."""
        self.user.is_staff = True
        self.user.save()
        sources = {
            NoteContentType.HTML: '<p>Source</p>',
            NoteContentType.JSON: ' {"n":9007199254740993}\n',
            NoteContentType.PLAIN_TEXT: '\n# Source\n<literal>&</literal>\n',
        }
        for template in [False, True]:
            for old_type, original in sources.items():
                data = self.create_note(old_type, original, template=template)
                url = reverse('api-note-detail', kwargs={'pk': data['pk']})
                for new_type, replacement in sources.items():
                    if old_type == new_type:
                        continue
                    for method in [self.patch, self.put]:
                        for replace_content in [False, True]:
                            with self.subTest(
                                template=template,
                                old=old_type,
                                new=new_type,
                                method=method.__name__,
                                replace_content=replace_content,
                            ):
                                payload = {
                                    'title': 'Rejected title',
                                    'content_type': new_type,
                                }
                                if replace_content:
                                    payload['content'] = replacement
                                response = method(url, payload, expected_code=400)
                                self.assertIn('content_type', response.data)
                                item = Note.objects.get(pk=data['pk'])
                                self.assertEqual(item.content_type, old_type)
                                self.assertEqual(item.content, original)
                                self.assertEqual(item.title, data['title'])

    def test_model_content_type_is_permanent(self):
        """Direct model saves cannot change type or validate content under another type."""
        self.user.is_staff = True
        self.user.save()
        for template in [False, True]:
            for old_type in NoteContentType.values:
                data = self.create_note(old_type, '{}', template=template)
                item = Note.objects.get(pk=data['pk'])
                for new_type in NoteContentType.values:
                    if old_type == new_type:
                        continue
                    for update_fields in [
                        None,
                        ['content_type', 'content'],
                        ['content'],
                    ]:
                        with self.subTest(
                            template=template,
                            old=old_type,
                            new=new_type,
                            update_fields=update_fields,
                        ):
                            item.content_type = new_type
                            item.content = '[]'
                            with self.assertRaises(ValidationError) as error:
                                item.save(update_fields=update_fields)
                            self.assertIn('content_type', error.exception.message_dict)
                            item.refresh_from_db()
                            self.assertEqual(item.content_type, old_type)
                            self.assertEqual(item.content, '{}')

    def test_same_type_and_omitted_type_do_not_reset(self):
        """Updates with an unchanged or omitted content type preserve content."""
        data = self.create_note(NoteContentType.JSON, ' [1, 2]\n')
        url = reverse('api-note-detail', kwargs={'pk': data['pk']})
        response = self.patch(
            url, {'content_type': NoteContentType.JSON}, expected_code=200
        )
        self.assertEqual(response.data['content'], ' [1, 2]\n')
        response = self.patch(url, {'content': ' [3]\n'}, expected_code=200)
        self.assertEqual(response.data['content_type'], NoteContentType.JSON)
        self.assertEqual(response.data['content'], ' [3]\n')
        response = self.patch(
            url,
            {'content_type': NoteContentType.JSON, 'content': '[]'},
            expected_code=200,
        )
        self.assertEqual(response.data['content'], '[]')

    def create_html_note_with_image(self):
        """Create an HTML note which references a real stored image."""
        data = self.create_note(NoteContentType.HTML, '')
        buf = io.BytesIO()
        Image.new('RGB', (2, 2)).save(buf, format='PNG')
        item = Note.objects.get(pk=data['pk'])
        image = NotesImage.objects.create(
            note=item,
            image=SimpleUploadedFile(
                'format.png', buf.getvalue(), content_type='image/png'
            ),
        )
        item.content = f'<p>Image</p><img src="{image.image.url}">'
        item.save()
        return item, image

    def test_rejected_format_changes_preserve_content_and_images(self):
        """API and model rejection leave the existing image records and files intact."""
        item, image = self.create_html_note_with_image()
        original = item.content
        url = reverse('api-note-detail', kwargs={'pk': item.pk})
        for new_type, content in [
            (NoteContentType.JSON, '{}'),
            (NoteContentType.PLAIN_TEXT, ''),
        ]:
            response = self.patch(
                url, {'content_type': new_type, 'content': content}, expected_code=400
            )
            self.assertIn('content_type', response.data)
            item.content_type = new_type
            item.content = content
            with self.assertRaises(ValidationError):
                item.save()
            item.refresh_from_db()
            self.assertEqual(item.content_type, NoteContentType.HTML)
            self.assertEqual(item.content, original)
            self.assertTrue(item.images.filter(pk=image.pk).exists())
            self.assertTrue(image.image.storage.exists(image.image.name))

    def test_rolled_back_image_cleanup_preserves_files(self):
        """Rolling back a note edit or deletion restores image rows and their files."""
        item, image = self.create_html_note_with_image()
        note_pk, image_pk = item.pk, image.pk
        original = item.content
        for delete_note in [False, True]:
            with self.subTest(delete_note=delete_note):
                with self.captureOnCommitCallbacks(execute=True):
                    with self.assertRaisesMessage(ValueError, 'Abort transaction'):
                        with transaction.atomic():
                            if delete_note:
                                item.delete()
                            else:
                                item.content = '<p>Image removed</p>'
                                item.save()
                            self.assertFalse(
                                NotesImage.objects.filter(pk=image_pk).exists()
                            )
                            self.assertTrue(
                                image.image.storage.exists(image.image.name)
                            )
                            raise ValueError('Abort transaction')

                item = Note.objects.get(pk=note_pk)
                self.assertEqual(item.content, original)
                self.assertTrue(item.images.filter(pk=image_pk).exists())
                self.assertTrue(image.image.storage.exists(image.image.name))

    def test_html_default_and_sanitization(self):
        """Notes default to HTML and sanitize submitted markup."""
        response = self.post(
            self.url,
            {
                'title': 'HTML',
                'model_type': 'part',
                'model_id': self.part.pk,
                'content': ' <p>Safe</p><script>alert(1)</script> ',
            },
            expected_code=201,
        )
        self.assertEqual(response.data['content_type'], NoteContentType.HTML)
        self.assertIn('<p>Safe</p>', response.data['content'])
        self.assertNotIn('<script>', response.data['content'])

    def test_size_limit(self):
        """Reject note content exceeding the model's size limit."""
        data = self.create_note(NoteContentType.PLAIN_TEXT, '')
        response = self.patch(
            reverse('api-note-detail', kwargs={'pk': data['pk']}),
            {'content': 'a' * (Note.NOTES_MAX_LENGTH + 1)},
            expected_code=400,
        )
        self.assertIn('content', response.data)

    def test_copy_and_report_preserve_raw_content(self):
        """Copies retain formats; reports escape source instead of interpreting it."""
        for content_type, content in [
            (
                NoteContentType.JSON,
                ' {"html":"</pre><img src=x onerror=alert(1)><script>alert(1)</script>","n":9007199254740993}\n',
            ),
            (
                NoteContentType.PLAIN_TEXT,
                '# Heading\n</pre><img src=x onerror=alert(1)><script>alert(1)</script>',
            ),
        ]:
            with self.subTest(content_type=content_type):
                self.part = Part.objects.create(name=f'Source {content_type}')
                self.create_note(content_type, content, primary=True)
                html = render_note(self.part)
                self.assertIn('<pre ', html)
                self.assertIn('&lt;script&gt;', html)
                self.assertNotIn('<script>', html)
                self.assertNotIn('<img ', html)
                self.assertEqual(html.count('</pre>'), 1)
                target = Part.objects.create(name=f'Copy {content_type}')
                target.copy_notes_from(self.part)
                copied = target.primary_note
                self.assertEqual(copied.content, content)
                self.assertEqual(copied.content_type, content_type)

    def test_raw_templates(self):
        """Templates carry the same raw content and format as regular notes."""
        self.user.is_staff = True
        self.user.save()
        for content_type, content in [
            (NoteContentType.JSON, ' {"a":1}\n'),
            (NoteContentType.PLAIN_TEXT, '# Template\n'),
        ]:
            data = self.create_note(content_type, content, template=True)
            source = self.get(
                reverse('api-note-detail', kwargs={'pk': data['pk']})
            ).data
            created = self.create_note(source['content_type'], source['content'])
            self.assertEqual(created['content'], content)
            self.assertEqual(created['content_type'], content_type)

    def test_raw_notes_reject_images(self):
        """Embedded images cannot be attached to a raw note through API or model."""
        for content_type in [NoteContentType.JSON, NoteContentType.PLAIN_TEXT]:
            data = self.create_note(content_type, '{}')
            buf = io.BytesIO()
            Image.new('RGB', (2, 2)).save(buf, format='PNG')
            image = SimpleUploadedFile(
                'note.png', buf.getvalue(), content_type='image/png'
            )
            response = self.post(
                reverse('api-notes-image-list'),
                {'note': data['pk'], 'image': image},
                format='multipart',
                expected_code=400,
            )
            self.assertIn('note', response.data)
            with self.assertRaises(ValidationError):
                NotesImage.objects.create(note_id=data['pk'], image='unused.png')

    def test_permission_is_unchanged(self):
        """Raw formats do not grant extra editing permission."""
        data = self.create_note(NoteContentType.JSON, '{}')
        self.clearRoles()
        self.assignRole('part.view')
        self.patch(
            reverse('api-note-detail', kwargs={'pk': data['pk']}),
            {'content': '[]'},
            expected_code=403,
        )
