import os

from django.conf import settings
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile

from rest_framework import status
from rest_framework.test import APITestCase

from ads.models import Ad, Category, AdReport
from ads.serializers import AdListSerializer, AdDetailSerializer, CategorySerializer, AdCreateOrUpdateSerializer


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

    def test_get_ads_list(self):
        response = self.client.get(reverse('ads:ads_list_api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.all().order_by('-datetime_created')
        serializer = AdListSerializer(ads_list, many=True)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)

    def test_get_ads_list_empty(self):
        self.ad1.active = self.ad2.active = False
        self.ad1.save()
        self.ad2.save()

        response = self.client.get(reverse('ads:ads_list_api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

        self.ad1.confirmation = self.ad2.confirmation = False
        self.ad1.save()
        self.ad2.save()

        response = self.client.get(reverse('ads:ads_list_api'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_get_categories_list(self):
        response = self.client.get(reverse('ads:categories_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        self.assertEqual(len(response.data), 2)
        self.assertEqual(response.data, serializer.data)

    def test_get_ads_list_with_category(self):
        response = self.client.get(reverse('ads:ads_list_with_category', args=[self.category1.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.filter(category=self.category1.pk)
        serializer = AdListSerializer(ads_list, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_get_ads_list_with_nonexistent_category(self):
        # Nonexistent category PK
        response = self.client.get(reverse('ads:ads_list_with_category', args=[999]))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('message', response.data)

    def test_search_ads(self):
        # try with title
        response = self.client.post(reverse('ads:search_ads'), {'q': 'text'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.filter(title__icontains='text')
        serializer = AdListSerializer(ads_list, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

        # try with text
        response = self.client.post(reverse('ads:search_ads'), {'q': 'CD'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.filter(text__icontains='CD')
        serializer = AdListSerializer(ads_list, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

        # try with category's name
        response = self.client.post(reverse('ads:search_ads'), {'q': 'two'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.filter(category__name__icontains='two')
        serializer = AdListSerializer(ads_list, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

    def test_search_ads_no_results(self):
        response = self.client.post(reverse('ads:search_ads'), {'q': self.ad2.pk}, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    def test_search_ads_invalid_data(self):
        response = self.client.post(reverse('ads:search_ads'), {'q': ''}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('q', response.data)

    def test_get_ad_detail(self):
        # active ad
        response = self.client.get(reverse('ads:ad_detail_api', args=[self.ad2.pk]), format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads_list = Ad.active_objs.get(pk=self.ad2.pk)
        serializer = AdDetailSerializer(ads_list)
        self.assertEqual(response.data, serializer.data)

        # inactive ad
        response = self.client.get(reverse('ads:ad_detail_api', args=[self.ad3.pk]), format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('message', response.data)

    def test_get_ad_detail_not_found(self):
        # An ad with this ID doesn't exist
        response = self.client.get(reverse('ads:ad_detail_api', args=[999]), format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_report_ad(self):
        # without login
        data = {
            'report_reason': 'This ad violates the terms of use.'
        }
        response = self.client.post(reverse('ads:report_ad_api', args=[self.ad1.pk]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # with login but ad is inactive
        self.client.force_authenticate(self.user1)

        data = {
            'report_reason': 'This ad violates the terms of use.'
        }
        # An ad with this ID doesn't exist
        response = self.client.post(reverse('ads:report_ad_api', args=[self.ad3.pk]), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

        # with login and ad active
        data = {
            'report_reason': 'This ad violates the terms of use.'
        }
        response = self.client.post(reverse('ads:report_ad_api', args=[self.ad1.pk]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        ad_report = AdReport.objects.first()
        self.assertIn('message', response.data)
        self.assertEqual(ad_report.ad, self.ad1)
        self.assertEqual(ad_report.user, self.user1)
        self.assertEqual(ad_report.report_reason, 'This ad violates the terms of use.')

    def test_report_ad_already_reported(self):
        self.client.force_authenticate(self.user1)

        AdReport.objects.create(ad=self.ad2, user=self.user1, report_reason='Test reason')

        data = {
            'report_reason': 'This ad violates the terms of use.'
        }
        response = self.client.post(reverse('ads:report_ad_api', args=[self.ad2.pk]), data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('message', response.data)

    def test_report_ad_not_found(self):
        self.client.force_authenticate(self.user2)

        data = {
            'report_reason': 'This ad violates the terms of use.'
        }
        # An ad with this ID doesn't exist
        response = self.client.post(reverse('ads:report_ad_api', args=[999]), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_delete_ad(self):
        # try without login
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad2.pk]), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # try with login but with user who is not the ad owner
        self.client.force_authenticate(self.user1)
        response = self.client.put(reverse('ads:update_ad_api', args=[self.ad2.pk]), format='multipart')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        # try with login with user who is the ad owner
        self.client.force_authenticate(self.user2)
        response = self.client.delete(reverse('ads:delete_ad_api', args=[self.ad2.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Retrieve the ad from the database and check if it is soft-deleted
        deleted_ad = Ad.objects.get(pk=self.ad2.pk)
        self.assertTrue(deleted_ad.is_delete)
        self.assertIsNotNone(deleted_ad.datetime_deleted)
        self.assertEqual(deleted_ad.delete_with, 'user')

    def test_delete_nonexistent_ad(self):
        self.client.force_authenticate(self.user2)
        # Attempt to delete an ad with a nonexistent PK
        response = self.client.delete(reverse('ads:delete_ad_api', args=[999]))

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_sign_and_unsign_ad(self):
        url = reverse('ads:sign_ad_api', args=[self.ad1.pk])

        # try without login
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

        # Make a GET request to sign the ad with login
        self.client.force_authenticate(self.user1)
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'add')

        # Check if the user is signed to the ad
        self.assertTrue(self.ad1.sign.filter(pk=self.user1.pk).exists())

        # Make another GET request to unsign the ad
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'remove')

        # Check if the user is not signed to the ad
        self.assertFalse(self.ad1.sign.filter(pk=self.user1.pk).exists())

    def test_sign_nonexistent_ad(self):
        # Attempt to sign/unsign an ad with a nonexistent PK
        self.client.force_authenticate(self.user1)
        url = reverse('ads:sign_ad_api', args=[999])
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('message', response.data)

    def test_user_sign_ads_list(self):
        # set sign
        self.ad1.sign.add(self.user1)
        self.ad3.sign.add(self.user1)

        url = reverse('ads:user_sign_ads_list_api')

        # login with user1 (user has signed ad1 and ad3)
        # Make a GET request to get the list of signed ads
        self.client.force_authenticate(self.user1)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        ads = Ad.active_objs.filter(sign=self.user1.pk)
        serializer = AdListSerializer(ads, many=True)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data, serializer.data)

        # login with user2 (user has not signed the ad)
        self.client.force_authenticate(self.user2)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])
