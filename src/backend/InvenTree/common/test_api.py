"""API unit tests for InvenTree common functionality."""

from unittest.mock import MagicMock, patch

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import override_settings
from django.urls import reverse

from PIL import Image
from rest_framework.test import APIClient

import common.models
from common.helpers import generate_image
from common.models import InvenTreeImage, InvenTreeSetting
from InvenTree.config import get_testfolder_dir
from InvenTree.unit_test import InvenTreeAPITestCase
from part.models import Part


class ParameterAPITests(InvenTreeAPITestCase):
    """Tests for the Parameter API."""

    roles = 'all'

    def test_template_options(self):
        """Test OPTIONS information for the ParameterTemplate API endpoint."""
        url = reverse('api-parameter-template-list')

        options = self.options(url)
        actions = options.data['actions']['GET']

        for field in [
            'pk',
            'name',
            'units',
            'description',
            'model_type',
            'selectionlist',
            'enabled',
        ]:
            self.assertIn(
                field,
                actions.keys(),
                f'Field "{field}" missing from ParameterTemplate API!',
            )

        model_types = [act['value'] for act in actions['model_type']['choices']]

        for mdl in [
            'part.part',
            'build.build',
            'company.company',
            'order.purchaseorder',
        ]:
            self.assertIn(
                mdl,
                model_types,
                f'Model type "{mdl}" missing from ParameterTemplate API!',
            )

    def test_parameter_options(self):
        """Test OPTIONS information for the Parameter API endpoint."""
        url = reverse('api-parameter-list')

        options = self.options(url)
        actions = options.data['actions']['GET']

        for field in [
            'pk',
            'template',
            'model_type',
            'model_id',
            'data',
            'data_numeric',
        ]:
            self.assertIn(
                field, actions.keys(), f'Field "{field}" missing from Parameter API!'
            )

        self.assertFalse(actions['data']['read_only'])
        self.assertFalse(actions['model_type']['read_only'])

    def test_template_api(self):
        """Test ParameterTemplate API functionality."""
        url = reverse('api-parameter-template-list')

        N = common.models.ParameterTemplate.objects.count()

        # Create a new ParameterTemplate - initially with invalid model_type field
        data = {
            'name': 'Test Parameter',
            'units': 'mm',
            'description': 'A test parameter template',
            'model_type': 'order.salesorderx',
            'enabled': True,
        }

        response = self.post(url, data, expected_code=400)
        self.assertIn('Content type not found', str(response.data['model_type']))

        data['model_type'] = 'order.salesorder'

        response = self.post(url, data, expected_code=201)
        pk = response.data['pk']

        # Verify that the ParameterTemplate was created
        self.assertEqual(common.models.ParameterTemplate.objects.count(), N + 1)

        template = common.models.ParameterTemplate.objects.get(pk=pk)
        self.assertEqual(template.name, 'Test Parameter')
        self.assertEqual(template.description, 'A test parameter template')
        self.assertEqual(template.units, 'mm')

        # Let's update the Template via the API
        data = {'description': 'An UPDATED test parameter template'}

        response = self.patch(
            reverse('api-parameter-template-detail', kwargs={'pk': pk}),
            data,
            expected_code=200,
        )

        template.refresh_from_db()
        self.assertEqual(template.description, 'An UPDATED test parameter template')

        # Finally, let's delete the Template
        response = self.delete(
            reverse('api-parameter-template-detail', kwargs={'pk': pk}),
            expected_code=204,
        )

        self.assertEqual(common.models.ParameterTemplate.objects.count(), N)
        self.assertFalse(common.models.ParameterTemplate.objects.filter(pk=pk).exists())

        # Let's create a template which does not specify a model_type
        data = {
            'name': 'Universal Parameter',
            'units': '',
            'description': 'A parameter template for all models',
            'enabled': False,
        }

        response = self.post(url, data, expected_code=201)

        self.assertIsNone(response.data['model_type'])
        self.assertFalse(response.data['enabled'])

    def test_template_filters(self):
        """Tests for API filters against ParameterTemplate endpoint."""
        from company.models import Company

        # Create some ParameterTemplate objects
        t1 = common.models.ParameterTemplate.objects.create(
            name='Template A',
            description='Template with choices',
            choices='apple,banana,cherry',
            enabled=True,
        )

        t2 = common.models.ParameterTemplate.objects.create(
            name='Template B',
            description='Template without choices',
            enabled=True,
            units='mm',
            model_type=Company.get_content_type(),
        )

        t3 = common.models.ParameterTemplate.objects.create(
            name='Template C', description='Another template', enabled=False
        )

        url = reverse('api-parameter-template-list')

        # Filter by 'enabled' status
        response = self.get(url, data={'enabled': True})
        self.assertEqual(len(response.data), 2)

        response = self.get(url, data={'enabled': False})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t3.pk)

        # Filter by 'has_choices'
        response = self.get(url, data={'has_choices': True})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t1.pk)

        response = self.get(url, data={'has_choices': False})
        self.assertEqual(len(response.data), 2)

        # Filter by 'model_type'
        response = self.get(url, data={'model_type': 'company.company'})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t2.pk)

        # Filter by 'has_units'
        response = self.get(url, data={'has_units': True})
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['pk'], t2.pk)

        response = self.get(url, data={'has_units': False})
        self.assertEqual(len(response.data), 2)

        # Filter by 'for_model'
        # Note that a 'blank' model_type is considered to match all models
        response = self.get(url, data={'for_model': 'part.part'})
        self.assertEqual(len(response.data), 2)

        response = self.get(url, data={'for_model': 'company'})
        self.assertEqual(len(response.data), 3)

        # Create a Parameter against a specific Company instance
        company = Company.objects.create(
            name='Test Company', description='A company for testing'
        )

        common.models.Parameter.objects.create(
            template=t1,
            model_type=company.get_content_type(),
            model_id=company.pk,
            data='apple',
        )

        model_types = {'company': 3, 'part.part': 2, 'order.purchaseorder': 2}

        for model_name, count in model_types.items():
            response = self.get(url, data={'for_model': model_name})
            self.assertEqual(
                len(response.data),
                count,
                f'Incorrect number of templates for model "{model_name}"',
            )

        # Filter with an invalid 'for_model'
        response = self.get(
            url, data={'for_model': 'invalid.modelname'}, expected_code=400
        )

        self.assertIn('Invalid content type: invalid.modelname', str(response.data))

        # Filter the "exists for model" filter
        model_types = {'company': 1, 'part.part': 0, 'order.purchaseorder': 0}

        for model_name, count in model_types.items():
            response = self.get(url, data={'exists_for_model': model_name})
            self.assertEqual(
                len(response.data),
                count,
                f'Incorrect number of templates for model "{model_name}"',
            )

    def test_parameter_api(self):
        """Test Parameter API functionality."""
        # Create a simple part to test with
        from part.models import Part

        part = Part.objects.create(name='Test Part', description='A part for testing')

        N = common.models.Parameter.objects.count()

        # Create a ParameterTemplate for the Part model
        template = common.models.ParameterTemplate.objects.create(
            name='Length',
            units='mm',
            model_type=part.get_content_type(),
            description='Length of part',
            enabled=True,
        )

        # Create a Parameter via the API
        url = reverse('api-parameter-list')

        data = {
            'template': template.pk,
            'model_type': 'part.part',
            'model_id': part.pk,
            'data': '25.4',
        }

        # Initially, user does not have correct permissions
        response = self.post(url, data=data, expected_code=403)

        self.assertIn(
            'User does not have permission to create or edit parameters for this model',
            str(response.data['detail']),
        )

        # Grant user the correct permissions
        self.assignRole('part.add')

        response = self.post(url, data=data, expected_code=201)

        parameter = common.models.Parameter.objects.get(pk=response.data['pk'])

        # Check that the Parameter was created
        self.assertEqual(common.models.Parameter.objects.count(), N + 1)

        # Try to create a duplicate Parameter (should fail)
        response = self.post(url, data=data, expected_code=400)

        self.assertIn(
            'The fields model_type, model_id, template must make a unique set.',
            str(response.data['non_field_errors']),
        )

        # Let's edit the Parameter via the API
        url = reverse('api-parameter-detail', kwargs={'pk': parameter.pk})

        response = self.patch(url, data={'data': '-2 inches'}, expected_code=200)

        # Ensure parameter conversion has correctly updated data_numeric field
        data = response.data
        self.assertEqual(data['data'], '-2 inches')
        self.assertAlmostEqual(data['data_numeric'], -50.8, places=2)

        # Finally, delete the Parameter via the API
        response = self.delete(url, expected_code=204)

        self.assertEqual(common.models.Parameter.objects.count(), N)
        self.assertFalse(
            common.models.Parameter.objects.filter(pk=parameter.pk).exists()
        )

    def test_parameter_annotation(self):
        """Test that we can annotate parameters against a queryset."""
        from company.models import Company

        templates = []
        parameters = []
        companies = []

        for ii in range(100):
            company = Company(
                name=f'Test Company {ii}',
                description='A company for testing parameter annotations',
            )
            companies.append(company)

        Company.objects.bulk_create(companies)

        # Let's create a large number of parameters
        for ii in range(25):
            templates.append(
                common.models.ParameterTemplate(
                    name=f'Test Parameter {ii}',
                    units='',
                    description='A parameter for testing annotations',
                    model_type=Company.get_content_type(),
                    enabled=True,
                )
            )

        common.models.ParameterTemplate.objects.bulk_create(templates)

        # Create a parameter for every company against every template
        for company in Company.objects.all():
            for template in common.models.ParameterTemplate.objects.all():
                parameters.append(
                    common.models.Parameter(
                        template=template,
                        model_type=company.get_content_type(),
                        model_id=company.pk,
                        data=f'Test data for {company.name} - {template.name}',
                    )
                )

        common.models.Parameter.objects.bulk_create(parameters)

        self.assertEqual(
            common.models.Parameter.objects.count(), len(companies) * len(templates)
        )

        # We will fetch the companies, annotated with all parameters
        url = reverse('api-company-list')

        # By default, we do not expect any parameter annotations
        response = self.get(url, data={'limit': 5})

        self.assertEqual(response.data['count'], len(companies))
        for company in response.data['results']:
            self.assertNotIn('parameters', company)

        # Fetch all companies, explicitly without parameters
        with self.assertNumQueriesLessThan(20):
            response = self.get(url, data={'parameters': False})

        # Now, annotate with parameters
        # This must be done efficiently, without an 1 + N query pattern
        with self.assertNumQueriesLessThan(45):
            response = self.get(url, data={'parameters': True})

        self.assertEqual(len(response.data), len(companies))

        for company in response.data:
            self.assertIn('parameters', company)
            self.assertEqual(
                len(company['parameters']),
                len(templates),
                'Incorrect number of parameter annotations found',
            )

    def test_parameter_delete(self):
        """Test that associated parameters are correctly deleted when removing the linked model."""
        from part.models import Part

        part = Part.objects.create(
            name='Test Part', description='A part for testing', active=False
        )

        # Create a ParameterTemplate for the Part model
        template = common.models.ParameterTemplate.objects.create(
            name='Test Parameter',
            description='A parameter template for testing parameter deletion',
            model_type=None,
        )

        # Create a Parameter for the Build
        parameter = common.models.Parameter.objects.create(
            template=template,
            model_type=part.get_content_type(),
            model_id=part.pk,
            data='Test data',
        )

        self.assertTrue(
            common.models.Parameter.objects.filter(pk=parameter.pk).exists()
        )

        N = common.models.Parameter.objects.count()

        # Now delete the part instance
        self.assignRole('part.delete')
        self.delete(
            reverse('api-part-detail', kwargs={'pk': part.pk}), expected_code=204
        )

        self.assertEqual(common.models.Parameter.objects.count(), N - 1)
        self.assertFalse(
            common.models.Parameter.objects.filter(template=template.pk).exists()
        )


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
        counts = {
            settings.MEDIA_URL + str(img.image): 1 for img in [self.img1, self.img2]
        }
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
