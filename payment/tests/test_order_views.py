from django.urls import reverse
from django.contrib.auth import get_user_model

from rest_framework import status
from rest_framework.test import APITestCase

from payment.models import Order, PackageAdToken
from payment.serializers import OrderReadSerializer


class OrderAPIViewsTest(APITestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user_model().objects.create_user(phone='9354214823')
        cls.user2 = get_user_model().objects.create_user(phone='9354211212')

        cls.package1 = PackageAdToken.objects.create(
            name='Test Package 1', description='Test Package 1 Description', price=100, token_quantity=5,
            confirmation=True
        )
        cls.package2 = PackageAdToken.objects.create(
            name='Test Package 2', description='Test Package 2 Description', price=200, token_quantity=10,
            confirmation=False
        )

    # Test for OrderRegistrationAPI
    def test_create_order(self):
        data = {
            'package': self.package1.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
            'order_note': 'Test order note',
        }

        # try without login
        response = self.client.post(reverse('payment:order_registration'), data, format='json')
        self.assertEqual(response.data.get('detail'), 'Authentication credentials were not provided.')

        # try with login
        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        order_created = Order.objects.first()
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Order.objects.count(), 1)
        self.assertEqual(order_created.customer, self.user1)
        self.assertEqual(order_created.created_by, self.user1)
        self.assertEqual(response.data['status'], 'Done')

    # Test for OrderRegistrationAPI
    def test_create_order_with_invalid_data(self):
        data = {
            'package': 12,
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(Order.objects.count(), 0)
        self.assertIsNotNone(response.data.get('package'))
        self.assertIsNotNone(response.data.get('first_name'))

    # Test for OrderRegistrationAPI
    def test_create_order_with_open_order(self):
        # Create an open order for the user1
        open_order = Order.objects.create(
            customer=self.user1, package=self.package1, completed=False
        )

        data = {
            'package': self.package1.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
            'order_note': 'Test order note',
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertIn('You have a open Order', response.data['message'])
        self.assertIn('update url', response.data)
        self.assertIn(reverse('payment:update_order', args=[open_order.pk]), response.data.get('update url'))

    # Test for OrderRegistrationAPI
    def test_create_order_invalid_package(self):
        # Set the package to be invalid for testing
        self.package1.is_delete = True
        self.package1.save()

        data = {
            'package': self.package1.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
            'order_note': 'Test order note',
        }

        self.client.force_authenticate(user=self.user1)
        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('package', response.data)

        # the package invalid for testing (confirmation=False)
        data = {
            'package': self.package2.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
            'order_note': 'Test order note',
        }

        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('package', response.data)

        # the package invalid for testing (is_deleted=True, confirmation=False)
        self.package2.is_delete = True
        self.package2.save()
        data = {
            'package': self.package2.pk,
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'johndoe@gmail.com',
            'phone': '9390125991',
            'order_note': 'Test order note',
        }

        response = self.client.post(reverse('payment:order_registration'), data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('package', response.data)

    # Test for UserOrdersListAPI
    def test_get_user_orders_list(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('payment:orders_list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        user_orders = Order.objects.filter(customer=self.user1.pk).order_by('-datetime_ordered')
        serializer = OrderReadSerializer(user_orders, many=True)
        self.assertEqual(response.data, serializer.data)

    # Test for OrderDetailAPI
    def test_get_order_detail(self):
        open_order = Order.objects.create(
            customer=self.user1, package=self.package1, first_name='John', last_name='Doe',
            phone='9390125991', completed=False,
        )

        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('payment:order_detail', args=[open_order.pk]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        serializer = OrderReadSerializer(open_order)
        self.assertEqual(response.data, serializer.data)

    # Test for OrderDetailAPI
    def test_get_nonexistent_order_detail(self):
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(reverse('payment:order_detail', args=[999]))  # non-existent PK
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        self.assertIn('There is no order with this pk', response.data.get('message'))

    # Test for OrderDetailAPI
    def test_owner_permission_in_order_detail(self):
        # create an open order with user1
        open_order = Order.objects.create(
            customer=self.user1, package=self.package1, first_name='John', last_name='Doe',
            phone='9390125991', completed=False,
        )

        self.client.force_authenticate(user=self.user2)  # login with user2
        response = self.client.get(reverse('payment:order_detail', args=[open_order.pk]))

        self.assertEqual(response.data.get('detail'), 'You do not have permission to perform this action.')

    # Test for UpdateOrderAPI
    def test_update_order(self):
        open_order = Order.objects.create(
            customer=self.user2, package=self.package1, first_name='AliReza', last_name='Brown',
            phone='9354211212', completed=False,
        )

        data = {
            'package': self.package1.pk,
            'first_name': 'AliReza',
            'last_name': 'Amiri',
            'phone': '9354896212',
            'completed': True,
            'email': 'ali@gmail.com',
            'order_note': 'I add this for test',
        }

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('payment:update_order', args=[open_order.pk]), data)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        updated_order = Order.objects.get(pk=open_order.pk)
        self.assertFalse(updated_order.completed)
        self.assertEqual(updated_order.last_name, data['last_name'])
        self.assertEqual(updated_order.phone.as_e164, '+98' + data['phone'])  # '+98' add code country to phone in data
        self.assertEqual(updated_order.email, data['email'])
        self.assertEqual(updated_order.order_note, data['order_note'])

    # Test for UpdateOrderAPI
    def test_update_nonexistent_order(self):
        Order.objects.create(
            customer=self.user2, package=self.package2, first_name='AliReza', last_name='Brown',
            phone='9354211212', completed=False,
        )

        data = {
            'customer': self.user2,
            'package': self.package1.pk,
            'first_name': 'AliReza',
            'last_name': 'Amiri',
            'phone': '9354896212',
            'completed': True,
            'email': 'ali@gmail.com',
            'order_note': 'I add this for test',
        }

        self.client.force_authenticate(user=self.user2)
        response = self.client.put(reverse('payment:update_order', args=[999]), data)  # non-existent PK
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('There is no order with this pk', response.data['message'])

    # Test for UpdateOrderAPI
    def test_owner_permission_in_update_order_(self):
        # create an open order with user1
        open_order = Order.objects.create(
            customer=self.user1, package=self.package1, first_name='AliReza', last_name='Brown',
            phone='9354211212', completed=False,
        )

        data = {
            'package': self.package1.pk,
            'first_name': 'AliReza',
            'last_name': 'Amiri',
            'phone': '9354896212',
            'completed': True,
            'email': 'ali@gmail.com',
            'order_note': 'I add this for test',
        }

        self.client.force_authenticate(user=self.user2)  # login with user2
        response = self.client.put(reverse('payment:update_order', args=[open_order.pk]), data)

        self.assertEqual(response.data.get('detail'), 'You do not have permission to perform this action.')
