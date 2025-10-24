"""testing InvenTreeImage API endpoints."""

from unittest.mock import MagicMock, patch

from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from PIL import Image
from rest_framework.test import APIClient

from common.helpers import generate_image
from common.models import InvenTreeImage, InvenTreeSetting
from InvenTree.config import get_testfolder_dir
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part


@override_settings(MEDIA_ROOT=get_testfolder_dir())
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

        # Create  target object (e.g. a Part) to attach images to
        cls.part1 = Part.objects.create(
            name='Test Part', description='A part for image tests'
        )

        cls.part2 = Part.objects.create(
            name='Test Part 2', description='Another part for image tests'
        )

        # Determine the ContentType for our Part model
        cls.content_type = ContentType.objects.get_for_model(Part)

        # Prepare two in memory image files
        cls.image_file_1 = generate_image('test1.png')
        cls.image_file_2 = generate_image('test2.png')

        # Create two images on the part
        cls.img1 = InvenTreeImage.objects.create(
            content_type=cls.content_type,
            object_id=cls.part1.pk,
            image=cls.image_file_1,
        )
        cls.img2 = InvenTreeImage.objects.create(
            content_type=cls.content_type,
            object_id=cls.part1.pk,
            image=cls.image_file_2,
        )

    def test_image_list_and_filtering(self):
        """Test listing images and filtering by object_id/primary."""
        url = reverse('api-image-list')

        # Should return both images
        response = self.get(url)
        self.assertEqual(len(response.data), 2)

        # Filter by object_id
        response = self.get(url, {'object_id': self.part1.pk})
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
        self.assertIn('thumbnail', response.data)
        self.assertIn('primary', response.data)
        # First created image should be primary by default
        self.assertTrue(response.data['primary'])

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

    def test_create_invalid_payload(self):
        """Test error responses when required fields are missing or invalid."""
        url = reverse('api-image-list')

        # Missing image file
        self.post(
            url, {'content_type': 'part', 'object_id': self.part1.pk}, expected_code=400
        )

        # Invalid content_type
        bad_file = SimpleUploadedFile('bad.png', b'123', content_type='image/png')
        response = self.post(
            url,
            {'content_type': 9999, 'object_id': self.part1.pk, 'image': bad_file},
            expected_code=400,
        )
        error_msg = str(response.data)
        self.assertIn('invalid', error_msg.lower())

    def test_existing_image_create_success(self):
        """Test creating an image with an existing image file."""
        file_name = self.img2.image.name
        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'existing_image': file_name,
        }

        response = self.upload_client.post(url, data, format='json')
        # Should be created
        self.assertEqual(response.status_code, 201, response.data)

        # Verify the DB record and its image path
        new_img = InvenTreeImage.objects.get(pk=response.data['pk'])
        # The stored image.name should end with our dummy filename
        self.assertTrue(str(new_img.image.name).endswith(file_name))

    def test_existing_image_invalid_file(self):
        """Test creating an image with non-existent file fails."""
        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'existing_image': 'nonexistent_image.png',
        }

        response = self.upload_client.post(url, data, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('does not exist', str(response.data))

    def test_thumbnail_list_endpoint(self):
        """Test the thumbnails list API endpoint."""
        url = reverse('api-uploadImageThumbs-list')

        # Thumbnails list should aggregate by image file with usage count
        response = self.get(url, expected_code=200)

        # Since we have exactly 2 unique image files, should return 2 entries
        self.assertEqual(len(response.data), 2)

        # Check that each entry has an 'image' and 'count'
        for entry in response.data:
            self.assertIn('image', entry)
            self.assertIn('count', entry)

        # The counts should match the actual usage
        counts = {str(img.image): 1 for img in [self.img1, self.img2]}
        for entry in response.data:
            img_name = entry['image']
            self.assertEqual(entry['count'], counts.get(img_name, 0))

        # Test filtering by object_id
        response = self.get(url, {'object_id': self.part1.pk}, expected_code=200)
        self.assertEqual(len(response.data), 2)  # Still both images

        # Test filtering for a non-existent object returns empty
        response = self.get(url, {'object_id': 99999}, expected_code=200)
        self.assertEqual(len(response.data), 0)

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

    def create_mock_image(self, format='PNG'):
        """Helper to create a mock PIL Image."""
        img = Image.new('RGB', (100, 100), color='red')
        return img

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_create_image_with_remote_url_success(self, mock_download):
        """Test creating an image from a valid remote URL."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        # Mock the download function to return a PIL Image
        mock_download.return_value = self.create_mock_image()

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': 'https://example.com/test-image.png',
        }

        response = self.post(url, data, expected_code=201)

        # Verify the download was called
        mock_download.assert_called_once_with('https://example.com/test-image.png')

        # Verify image was created
        self.assertIn('pk', response.data)
        image_id = response.data['pk']

        # Verify the image instance exists
        img = InvenTreeImage.objects.get(pk=image_id)
        self.assertEqual(img.object_id, self.part1.pk)
        self.assertTrue(img.image)  # Image file should be saved

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_create_image_remote_url_disabled(self, mock_download):
        """Test that remote image download fails when setting is disabled."""
        # Disable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', False, None)

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': 'https://example.com/test-image.png',
        }

        response = self.post(url, data, expected_code=400)

        # Should not attempt download
        mock_download.assert_not_called()

        # Check error message
        self.assertIn('remote_image', response.data)
        self.assertIn('not enabled', str(response.data['remote_image']))

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_create_image_remote_url_download_fails(self, mock_download):
        """Test handling of failed remote image download."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        # Mock download to raise an exception
        mock_download.side_effect = Exception('Network error')

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': 'https://example.com/invalid-image.png',
        }

        response = self.post(url, data, expected_code=400)

        # Verify error message
        self.assertIn('remote_image', response.data)
        self.assertIn('Failed to download', str(response.data['remote_image']))

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_update_image_with_remote_url(self, mock_download):
        """Test updating an existing image with a remote URL."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        # Create initial image
        img = InvenTreeImage.objects.create(
            content_type=self.content_type,
            object_id=self.part1.pk,
            image=generate_image('initial.png'),
        )

        # Mock download
        mock_download.return_value = self.create_mock_image()

        url = reverse('api-image-detail', kwargs={'pk': img.pk})
        data = {'remote_image': 'https://example.com/new-image.png'}

        self.patch(url, data, expected_code=200)

        # Verify download was called
        mock_download.assert_called_once()

        # Refresh from DB and verify image was updated
        img.refresh_from_db()
        self.assertTrue(img.image)

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_remote_image_processing_error(self, mock_download):
        """Test handling of image processing errors after download."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        # Create a mock image that will fail during save
        mock_img = MagicMock(spec=Image.Image)
        mock_img.format = 'PNG'
        mock_img.save.side_effect = Exception('Save failed')
        mock_download.return_value = mock_img

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': 'https://example.com/test-image.png',
        }

        response = self.post(url, data, expected_code=400)

        # Should get validation error about processing
        self.assertIn('Failed to process remote image', str(response.data))

    def test_create_without_any_image_source(self):
        """Test that creating without image, existing_image, or remote_image fails."""
        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            # No image source provided
        }

        response = self.post(url, data, expected_code=400)

        # Should require at least one image source
        error_msg = str(response.data)
        self.assertIn('image', error_msg.lower())

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_remote_image_empty_url(self, mock_download):
        """Test providing an empty remote_image URL."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': '',  # Empty URL
        }

        self.post(url, data, expected_code=400)

        # Should not call download for empty URL
        mock_download.assert_not_called()

    @patch('InvenTree.helpers_model.download_image_from_url')
    def test_remote_image_invalid_url_format(self, mock_download):
        """Test providing an invalid URL format."""
        # Enable the setting
        InvenTreeSetting.set_setting('INVENTREE_DOWNLOAD_FROM_URL', True, None)

        url = reverse('api-image-list')
        data = {
            'content_type': 'part',
            'object_id': self.part1.pk,
            'remote_image': 'not-a-valid-url',
        }

        response = self.post(url, data, expected_code=400)

        # Should fail URL validation before attempting download
        self.assertIn('remote_image', response.data)
