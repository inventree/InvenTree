"""testing InvenTreeImage API endpoints."""

import shutil
import tempfile

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from rest_framework.test import APIClient

from common.helpers import generate_image
from common.models import InvenTreeImage
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part


class ImageTestMixin:
    """Mixin for testing part images."""


@override_settings(MEDIA_ROOT=tempfile.mkdtemp(prefix='inventree_test_media_'))
class InvenTreeImageTest(InvenTreeAPITestCase):
    """Series of tests for the InvenTreeImage DRF API."""

    # Grant ourselves permission to add/change/delete parts
    roles = ['part.add', 'part.change', 'part.delete']

    @classmethod
    def setUpTestData(cls):
        """Custom setup routine for this class."""
        super().setUpTestData()

        # Create a custom APIClient for file uploads
        # Ref: https://stackoverflow.com/questions/40453947/how-to-generate-a-file-upload-test-request-with-django-rest-frameworks-apireq
        cls.upload_client = APIClient()
        cls.upload_client.force_authenticate(user=cls.user)

        # Create a target object (e.g. a Part) to attach images to
        cls.part = Part.objects.create(
            name='Test Part', description='A part for image tests'
        )

        # Determine the ContentType for our Part model
        cls.content_type = ContentType.objects.get_for_model(Part)

        # Prepare two in memory image files
        cls.image_file_1 = generate_image('test1.png')
        cls.image_file_2 = generate_image('test2.png')

        # Create two images on the part
        cls.img1 = InvenTreeImage.objects.create(
            content_type=cls.content_type,
            object_id=cls.part.pk,
            image=cls.image_file_1,
            primary=True,
        )
        cls.img2 = InvenTreeImage.objects.create(
            content_type=cls.content_type,
            object_id=cls.part.pk,
            image=cls.image_file_2,
            primary=True,
        )

    @classmethod
    def setUpClass(cls):
        """Custom setup routine for this class."""
        super().setUpClass()
        # Create a temp dir and override MEDIA_ROOT to point there
        cls._temp_media = tempfile.mkdtemp(prefix='invenree_test_media_')
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        """Custom teardown routine for this class."""
        # Disable the override first (restores original MEDIA_ROOT)
        cls._override.disable()
        # Remove everything in the temp dir
        shutil.rmtree(cls._temp_media, ignore_errors=True)

        super().tearDownClass()

    def test_image_list_and_filtering(self):
        """Test listing images and filtering by object_id/primary."""
        url = reverse('api-image-list')

        # Should return both images
        response = self.get(url)
        self.assertEqual(len(response.data), 2)

        # Filter by object_id
        response = self.get(url, {'object_id': self.part.pk})
        self.assertEqual(len(response.data), 2)

        # Only one image should be primary
        response = self.get(url, {'primary': False})
        self.assertEqual(len(response.data), 1)

    def test_image_detail_fields(self):
        """Test the detail endpoint returns expected fields."""
        url = reverse('api-image-detail', kwargs={'pk': self.img1.pk})
        response = self.get(url, expected_code=200)

        self.assertIn('pk', response.data)
        self.assertEqual(response.data['pk'], self.img1.pk)
        self.assertIn('image', response.data)
        self.assertFalse(response.data['primary'])

    def test_set_primary_toggles_siblings(self):
        """Patching primary=True should unset it on all other siblings."""
        url1 = reverse('api-image-detail', kwargs={'pk': self.img1.pk})
        url2 = reverse('api-image-detail', kwargs={'pk': self.img2.pk})

        # Set img1 to primary
        response = self.patch(url1, {'primary': True}, expected_code=200)
        self.assertTrue(response.data['primary'])

        # img2 should still be False
        resp2 = self.get(url2, expected_code=200)
        self.assertFalse(resp2.data['primary'])

        # Now set img2 to primary
        response = self.patch(url2, {'primary': True}, expected_code=200)
        self.assertTrue(response.data['primary'])

        # img1 should now have primary=False
        resp1 = self.get(url1, expected_code=200)
        self.assertFalse(resp1.data['primary'])

    def test_delete_primary_reassigns_successor(self):
        """Test deleting a primary image reassigns primary to another image."""
        # Mark img1 as primary
        self.img1.primary = True
        self.img1.save()

        # Delete img1
        url1 = reverse('api-image-detail', kwargs={'pk': self.img1.pk})
        self.delete(url1, expected_code=204)

        # Now img2 should exist and be primary
        url2 = reverse('api-image-detail', kwargs={'pk': self.img2.pk})
        response = self.get(url2, expected_code=200)
        self.assertTrue(response.data['primary'])

    def test_create_invalid_payload(self):
        """Test error responses when required fields are missing or invalid."""
        url = reverse('api-image-list')

        # Missing image file
        response = self.post(
            url, {'content_type': 'part', 'object_id': self.part.pk}, expected_code=400
        )
        self.assertIn('image', response.data)

        # Invalid content_type
        bad_file = SimpleUploadedFile('bad.png', b'123', content_type='image/png')
        response = self.post(
            url,
            {'content_type': 9999, 'object_id': self.part.pk, 'image': bad_file},
            expected_code=400,
        )
        self.assertIn('content_type', response.data)

    def test_existing_image_create_success(self):
        """Test creating an image with an existing image file."""
        file_name = self.img1.image.name
        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part.pk,
            'existing_image': file_name,
        }

        response = self.upload_client.post(url, data, format='json')
        # Should be created
        self.assertEqual(response.status_code, 201, response.data)

        # The response should echo back the existing_image field
        self.assertIn('existing_image', response.data)
        self.assertEqual(response.data['existing_image'], file_name)

        # Verify the DB record and its image path
        new_img = InvenTreeImage.objects.get(pk=response.data['pk'])
        # The stored image.name should end with our dummy filename
        self.assertTrue(str(new_img.image.name).endswith(file_name))
