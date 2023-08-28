import os

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase

from ads.models import Ad, Category


def image_for_test():
    image_path = os.path.join(settings.STATICFILES_DIRS[0], 'image/test/1.jpg')

    with open(image_path, 'rb') as image_file:
        image = SimpleUploadedFile(
            name='1.jpg',
            content=image_file.read(),
            content_type='image/jpeg'
        )
        return image


class AdsListAPITest(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user_model().objects.create_user(phone='9354214823')
        cls.user2 = get_user_model().objects.create_user(phone='9359048320')

        cls.category1 = Category.objects.create(
            name='Category one',
        )

        cls.category2 = Category.objects.create(
            name='Category two',
        )

        cls.ad1 = Ad.objects.create(
            author=cls.user1,
            title='Ad Title for text',
            text='this ad create for test',
            image='ad_image_1.jpg',
            status_product='new',
            phone='9351212121',
            price=10_000,
            location='Test Location 1',
            active=True,
            confirmation=True,
        )

        cls.ad2 = Ad.objects.create(
            author=cls.user2,
            title='shoes for happy mens',
            text='you can by CD',
            image='ad_image_1.jpg',
            status_product='new',
            price=10_000,
            location='Test Location 1',
            active=True,
            confirmation=True,
        )

        cls.ad3 = Ad.objects.create(
            author=cls.user2,
            title='still testing',
            text='please active this ad',
            image='ad_image_2.jpg',
            status_product='worked',
            price=20_000,
            location='Test Location 2',
            active=True,
        )

        cls.ad1.category.add(cls.category1)
        cls.ad2.category.add(cls.category2)
        cls.ad3.category.add(cls.category1)

    def test_create_ad_with_valid_data_and_test_token_ad(self):
        # try without login
        data = {
            'title': 'Test Ad',
            'text': 'This is a test ad.',
            'status_product': 'New',
            'price': 10_000,
            'phone': '9359048320',
            'location': 'Iran',
            'category': [self.category1.name, self.category2.pk],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try with login
        self.client.force_authenticate(self.user2)

        image = image_for_test()
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ad_created = Ad.objects.last()
        self.assertEqual(response.data.get('status'), 'Wait for confirmation')
        self.assertEqual(ad_created.text, 'This is a test ad.')
        self.assertIsNotNone(ad_created.image)
        self.assertEqual(ad_created.status_product, 'new')
        self.assertEqual(list(ad_created.category.all()), [self.category1, self.category2])

        # The free quota is over
        image = image_for_test()
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('You have reached your ad creation limit.', response.data.get('message'))

        # send wrong use
        image = image_for_test()
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api') + '?use=true', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('Send \'use\' like this use=True', response.data.get('message'))

        # send request for creating an ad without any ad token
        image = image_for_test()
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api') + '?use=True', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('you have not ad token', response.data.get('message'))

        # increase user2's ad token
        self.user2.ad_token = 2
        self.user2.save()

        # send request with difference phone but use an ad token
        image = image_for_test()
        data['image'] = image
        data['category'] = [12]

        # before using an ad token must be False
        self.assertFalse(self.user2.token_activated)
        self.assertEqual(self.user2.ad_token, 2)

        response = self.client.post(reverse('ads:create_ad_api') + '?use=True', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # after using an ad token must be True
        self.user2.refresh_from_db()
        self.assertTrue(self.user2.token_activated)
        self.assertEqual(self.user2.ad_token, 1)

        # send request
        image = image_for_test()
        data['image'] = image
        # set valid value for category
        data['category'].pop()

        response = self.client.post(reverse('ads:create_ad_api') + '?use=True', data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # after creating an ad must be False and an ad token mustn't change
        self.user2.refresh_from_db()
        self.assertFalse(self.user2.token_activated)
        self.assertEqual(self.user2.ad_token, 1)

    def test_create_ad_with_different_phone_with_user(self):
        self.client.force_authenticate(self.user2)

        # send request with different phone number
        image = image_for_test()
        data = {
            'title': 'Test Ad',
            'text': 'This is a test ad.',
            'image': image,
            'status_product': 'New',
            'price': 10_000,
            'phone': '09223587946',  # different phone with user1.phone
            'location': 'Iran',
            'category': [self.category1.name, self.category2.pk],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # test for send again code verify
        image = image_for_test()
        data['send_again'] = True
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(self.user2.codeverify.count_otp, 3)

        # send empty code
        image = image_for_test()
        data.pop('send_again')
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('code', response.data)

        # send wrong code
        image = image_for_test()
        data['code'] = 1111111
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('code'), 'wrong code')

        # send correct code
        image = image_for_test()
        data['code'] = self.user2.codeverify.code
        data['image'] = image

        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_ad_with_cancel_option(self):
        self.client.force_authenticate(self.user1)

        # send cancel without request to create an ad with different phone
        response = self.client.post(reverse('ads:create_ad_api') + '?cancel=True')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('status'), 'fail')
        self.assertEqual(response.data.get('message'), 'You did not request for create a ad yet')

        # send cancel without value except True
        response = self.client.post(reverse('ads:create_ad_api') + '?cancel=Tr')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('status'), 'fail')
        self.assertEqual(response.data.get('message'), 'send True for params cancel')

        # send request to create an ad
        image = image_for_test()
        data = {
            'title': 'Test Ad',
            'text': 'This is a test ad.',
            'image': image,
            'status_product': 'New',
            'price': 10_000,
            'phone': '09361212125',  # different phone with user1.phone
            'location': 'Iran',
            'category': [self.category1.name, self.category2.pk],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # send cancel correctly
        response = self.client.post(reverse('ads:create_ad_api') + '?cancel=True', data, format='multipart', )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('status'), 'cancel')

    def test_create_ad_with_invalid_data(self):
        self.client.force_authenticate(self.user1)
        data = {
            # Incomplete data, missing 'text' and invalid phone number
            'title': 'Test Ad',
            'status_product': 'newa',
            'price': 10000,
            'phone': '9354214823',
            'location': 'Test Location',
            'category': ['Category 1', 999],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('text', response.data)  # Expect an error message for missing 'text'
        self.assertIn('status_product', response.data)  # Expect an error message for invalid phone
        self.assertIn('image', response.data)  # Expect an error message for invalid phone

        # send data with an invalid category list with invalid name
        image = image_for_test()
        data = {
            'title': 'Test Ad',
            'text': 'This is a test ad.',
            'image': image,
            'status_product': 'New',
            'price': 10_000,
            'phone': '9354214823',
            'location': 'Iran',
            'category': ['does not exists'],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

        # send data with an invalid category list with invalid pk
        image = image_for_test()
        data = {
            'title': 'Test Ad',
            'text': 'This is a test ad.',
            'image': image,
            'status_product': 'New',
            'price': 10_000,
            'phone': '9354214823',
            'location': 'Iran',
            'category': [999],
            'active': True,
        }
        response = self.client.post(reverse('ads:create_ad_api'), data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('category', response.data)

    def test_update_ad(self):
        # try without login
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try with login but with user who is not the ad owner
        self.client.force_authenticate(self.user2)
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # try with login with user who is the ad owner
        self.client.force_authenticate(self.user1)
        image = image_for_test()
        # try with ad phone number
        updated_data = {
            'title': 'Updated Test Ad',
            'text': 'Updated ad text.',
            'image': image,
            'status_product': 'Worked',
            'price': 15_000,
            'phone': '9351212121',
            'location': 'Updated location',
            'category': [],  # Update or remove categories as needed
            'active': False,
        }

        # Make a PUT request to update the ad
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), updated_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the updated ad from the database
        updated_ad = Ad.objects.get(pk=self.ad1.pk)

        # Compare the updated fields with the updated data
        self.assertEqual(updated_ad.title, updated_data['title'])
        self.assertEqual(updated_ad.price, updated_data['price'])
        self.assertEqual(updated_ad.active, updated_data['active'])

        updated_data['title'] = 'this title is for ad1 (updated)'
        updated_data['text'] = 'use user phone number'
        updated_data['phone'] = '9354214823'
        updated_data['image'] = image_for_test()

        # Make a PUT request to update the ad
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), updated_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the updated ad from the database
        updated_ad = Ad.objects.get(pk=self.ad1.pk)

        # Compare the updated fields with the updated data
        self.assertEqual(updated_ad.title, updated_data['title'])
        self.assertEqual(updated_ad.text, updated_data['text'])
        # add country code to phone in updated_data
        self.assertEqual(updated_ad.phone.as_e164, '+98' + updated_data['phone'])

        updated_data['title'] = 'Using the previous number of the ad'
        updated_data['text'] = 'ad must not update because now ad phone is user phone'
        updated_data['phone'] = '9351212121'
        updated_data['image'] = image_for_test()

        # Make a PUT request to update the ad
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), updated_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the updated ad from the database
        updated_ad = Ad.objects.get(pk=self.ad1.pk)

        # Compare the updated fields with the updated data
        self.assertNotEqual(updated_ad.title, updated_data['title'])
        self.assertNotEqual(updated_ad.text, updated_data['text'])
        # add country code to phone in updated_data
        self.assertNotEqual(updated_ad.phone.as_e164, '+98' + updated_data['phone'])

    def test_update_ad_with_different_phone_with_user_and_ad(self):
        self.client.force_authenticate(self.user1)

        # Define the updated data
        image = image_for_test()
        updated_data = {
            'title': 'Updated Test Ad',
            'text': 'Updated ad text.',
            'image': image,
            'status_product': 'Worked',
            'price': 15_000,
            'phone': '9351110000',  # different phone number
            'location': 'Updated location',
            'category': [self.category2.name],
            'active': False,
        }

        # Make a PUT request to update the ad
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), updated_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the updated ad from the database
        updated_ad = Ad.objects.get(pk=self.ad1.pk)

        # Compare the updated fields with the updated data
        self.assertNotEqual(updated_ad.title, updated_data['title'])
        self.assertNotEqual(updated_ad.active, updated_data['active'])

        updated_data['code'] = self.user1.codeverify.code
        updated_data['image'] = image_for_test()

        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad1.pk]), updated_data, format='multipart')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the updated ad from the database
        updated_ad = Ad.objects.get(pk=self.ad1.pk)

        # Compare the updated fields with the updated data
        self.assertEqual(updated_ad.title, updated_data['title'])
        self.assertEqual(updated_ad.active, updated_data['active'])

    def test_update_nonexistent_ad(self):
        self.client.force_authenticate(self.user2)

        # Attempt to update an ad with a nonexistent PK
        image = image_for_test()
        # try with ad phone number
        updated_data = {
            'title': 'Updated Test Ad',
            'text': 'Updated ad text.',
            'image': image,
            'status_product': 'Worked',
            'price': 15_000,
            'phone': '9351212121',
            'location': 'Updated location',
            'category': [],  # Update or remove categories as needed
            'active': False,
        }

        response = self.client.put(reverse('ads:update_ad_api', args=[999]), updated_data, format='multipart')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
