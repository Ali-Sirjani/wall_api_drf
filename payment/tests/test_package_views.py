from django.urls import reverse

from rest_framework import status
from rest_framework.test import APITestCase

from payment.models import PackageAdToken
from payment.serializers import PackageAdTokenSerializer


class PackageAdTokenAPIViewsTest(APITestCase):
    def setUp(self):
        self.package1 = PackageAdToken.objects.create(
            name='Package 1', description='Description 1', price=100, token_quantity=10, confirmation=True
        )
        self.package2 = PackageAdToken.objects.create(
            name='Package 2', description='Description 2', price=200, token_quantity=20, confirmation=True,
        )
        self.package3 = PackageAdToken.objects.create(
            name='confirmation and is_deleted are False Package',
            description='confirmation and is_deleted are False Description', price=300, token_quantity=5,
            confirmation=False, is_delete=False
        )
        self.package4 = PackageAdToken.objects.create(
            name='confirmation and is_deleted are True Package',
            description='confirmation and is_deleted are True Description', price=400, token_quantity=6,
            confirmation=True, is_delete=True
        )
        self.package5 = PackageAdToken.objects.create(
            name='confirmation is False and is_delete is True Package',
            description='confirmation is False and is_delete is True Description', price=300, token_quantity=7,
            confirmation=False, is_delete=True
        )

    # Test for PackageAdTokenListAPI
    def test_get_active_packages(self):
        response = self.client.get(reverse('payment:packages_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        active_packages = PackageAdToken.active_objs.all()
        serializer = PackageAdTokenSerializer(active_packages, many=True)
        self.assertEqual(response.data, serializer.data)

    # Test for PackageAdTokenListAPI
    def test_get_active_packages_empty(self):
        # Delete all active packages
        PackageAdToken.active_objs.all().delete()

        response = self.client.get(reverse('payment:packages_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, [])

    # Test for PackageAdTokenListAPI
    def test_get_inactive_packages(self):
        response = self.client.get(reverse('payment:packages_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # packages with confirmation=True and is_delete=True
        packages_conf_del_true = PackageAdToken.objects.filter(confirmation=True, is_delete=True)
        serializer = PackageAdTokenSerializer(packages_conf_del_true, many=True)
        self.assertNotEqual(response.data, serializer.data)

        # packages with confirmation=False and is_delete=False
        packages_conf_del_false = PackageAdToken.objects.filter(confirmation=False, is_delete=False)
        serializer = PackageAdTokenSerializer(packages_conf_del_false, many=True)
        self.assertNotEqual(response.data, serializer.data)

        # packages with confirmation=False and is_delete=True
        packages_conf_false = PackageAdToken.objects.filter(confirmation=False, is_delete=True)
        serializer = PackageAdTokenSerializer(packages_conf_false, many=True)
        self.assertNotEqual(response.data, serializer.data)
