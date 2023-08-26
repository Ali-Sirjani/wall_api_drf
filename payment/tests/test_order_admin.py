from django.contrib import admin
from django.contrib.auth.models import Permission
from django.contrib.auth import get_user_model
from django.test import TestCase

from payment.admin import OrderAdmin
from payment.models import Order, PackageAdToken


class OrderAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user_model().objects.create_superuser(username='admin', password='admin')

        cls.user2 = get_user_model().objects.create_superuser(username='staff', password='staff')
        cls.user2.is_superuser = False
        permission_list = [
            Permission.objects.get(codename='add_order', content_type__app_label='payment'),
            Permission.objects.get(codename='change_order', content_type__app_label='payment'),
            Permission.objects.get(codename='delete_order', content_type__app_label='payment'),
        ]
        cls.user2.user_permissions.add(*permission_list)
        cls.user2.save()

        cls.package1 = PackageAdToken.objects.create(name='Token 1', description='this is package Token 1',
                                                     price=20_000, token_quantity=2, confirmation=True)
        cls.package2 = PackageAdToken.objects.create(name='Token 2', description='this is package Token 2',
                                                     price=40_000, discount=True, discount_price=38_000,
                                                     token_quantity=4, confirmation=True)
        cls.package3 = PackageAdToken.objects.create(name='Token 3', description='this is package Token 3',
                                                     price=100_000, discount=True, discount_price=50_000,
                                                     token_quantity=12)

        cls.order1 = Order.objects.create(
            customer=cls.user1,
            package=cls.package1,
            completed=False,
            first_name='Ali',
            last_name='Blue',
            email='john@gmail.com',
            phone='1234567890',
            order_note='Test note'
        )

        cls.order2 = Order.objects.create(
            customer=cls.user2,
            package=cls.package2,
            completed=True,
            first_name='elizabeth',
            last_name='Red',
            phone='9304567890',
        )

    def setUp(self):
        self.client.post('/admin/login/', {'username': self.user1.username, 'password': 'admin'})

    def test_get_fieldsets(self):
        order_admin = OrderAdmin(model=Order, admin_site=admin.site)
        request = self.client.get('/admin/payment/order/add/')
        fieldsets = order_admin.get_fieldsets(request)
        expected_fieldsets = (
            ('Order info', {
                'fields': (
                    'customer', 'package', 'first_name', 'last_name', 'email', 'phone', 'order_note', 'completed'),
            }),
        )
        self.assertEqual(fieldsets, expected_fieldsets)

    # Write similar tests for other admin methods like has_change_permission, get_readonly_fields, etc.

    def test_creat_order(self):
        # can't create an order with package.confirmation = False
        response = self.client.post('/admin/payment/order/add/', {
            'customer': self.user1.pk,
            'package': self.package3.pk,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@gmail.com',
            'phone': '9150648561',
            'order_note': 'Another note',
            'completed': True,
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/admin/payment/order/add/', {
            'customer': self.user1.pk,
            'package': self.package2.pk,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@gmail.com',
            'phone': '9150648561',
            'order_note': 'Another note',
            'completed': True,
            # send data wrong data for package info in order
            'price': 150,
            'discount': False,  # in package the discount is True
            'discount_price': 200,
            'token_quantity': 50,
        })
        self.assertEqual(response.status_code, 302)

        new_order1 = Order.objects.last()
        self.assertEqual(new_order1.created_by, self.user1)
        self.assertEqual(new_order1.package, self.package2)
        self.assertEqual(new_order1.first_name, 'Jane')
        self.assertEqual(new_order1.phone, '+989150648561')
        self.assertTrue(new_order1.completed)
        # check package info in order
        self.assertNotEqual(new_order1.price, 150)
        self.assertNotEqual(new_order1.discount, False)
        self.assertNotEqual(new_order1.discount_price, 200)
        self.assertNotEqual(new_order1.token_quantity, 50)

        # login with staff user
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})
        response = self.client.post('/admin/payment/order/add/', {
            'customer': self.user2.pk,
            'package': self.package1.pk,
            'first_name': 'Ben',
            'last_name': 'Brown',
            'email': 'ben@gmail.com',
            'phone': '9150645656',
            'completed': True,
            # send data wrong data for package info in order
            'price': 600,
            'discount': True,  # in package the discount is True
            'discount_price': 200,
            'token_quantity': 20,
        })
        self.assertEqual(response.status_code, 302)

        new_order2 = Order.objects.last()
        self.assertEqual(new_order2.created_by, self.user2)
        self.assertEqual(new_order2.package, self.package1)
        self.assertEqual(new_order2.first_name, 'Ben')
        self.assertEqual(new_order2.phone, '+989150645656')
        # completed must be false for user that has not permission
        self.assertFalse(new_order2.completed)
        # check package info in order
        self.assertNotEqual(new_order2.price, 600)
        self.assertNotEqual(new_order2.discount, True)
        self.assertNotEqual(new_order2.discount_price, 200)
        self.assertNotEqual(new_order2.token_quantity, 20)

    def test_change_order(self):
        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user1.pk,
            'package': self.package3.pk,
            'first_name': 'Ali',
            'last_name': 'Blue',
            'email': 'john@gmail.com',
            'phone': '1234567890',
            'order_note': 'Test note',
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user2.pk,
            'package': self.package1.pk,
            'first_name': 'Ali',
            'last_name': 'Blue',
            'email': 'john@gmail.com',
            'phone': '1234567890',
            'order_note': 'Test note',
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user1.pk,
            'package': self.package1.pk,
            'first_name': 'Jane',
            'last_name': 'Doe',
            'email': 'jane@gmail.com',
            'phone': '9150648561',
            'order_note': 'Another note',
            'completed': True,
        })
        self.assertEqual(response.status_code, 302)

        self.order1.refresh_from_db()
        self.assertTrue(self.order1.completed)
        self.assertEqual(self.order1.completed_by, self.user1)
        self.assertEqual(self.order1.edited_by, self.user1)
        self.assertEqual(self.order1.package, self.package1)
        self.assertEqual(self.order1.first_name, 'Jane')

        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user1.pk,
            'package': self.package2.pk,
            'first_name': 'Ali',
            'last_name': 'Blue',
            'email': 'john@gmail.com',
            'phone': '09150641213',
            'order_note': 'Test note',
            'completed': True,
        })
        self.assertEqual(response.status_code, 302)

        self.order1.refresh_from_db()
        self.assertTrue(self.order1.completed)
        self.assertEqual(self.order1.completed_by, self.user1)
        self.assertNotEqual(self.order1.package, self.package2)
        self.assertNotEqual(self.order1.first_name, 'Ali')

        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user1.pk,
            'package': self.package2.pk,
            'first_name': 'Ali',
            'last_name': 'Blue',
            'email': 'john@gmail.com',
            'phone': '09150641213',
            'order_note': 'Test note',
            'completed': False,
        })
        self.assertEqual(response.status_code, 302)

        self.order1.refresh_from_db()
        self.assertFalse(self.order1.completed)
        self.assertEqual(self.order1.completed_by, self.user1)
        self.assertEqual(self.order1.uncompleted_by, self.user1)
        self.assertEqual(self.order1.package, self.package2)
        self.assertEqual(self.order1.first_name, 'Ali')

        # login with staff user
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})

        # change order with completed = False
        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/change/', {
            'customer': self.user1.pk,
            'package': self.package2.pk,
            'first_name': 'Reza',
            'last_name': 'Blue',
            'email': 'john@gmail.com',
            'phone': '09150641213',
            'order_note': 'we just change this and first name',
        })

        self.order1.refresh_from_db()
        self.assertFalse(self.order1.completed)
        self.assertEqual(self.order1.completed_by, self.user1)
        self.assertEqual(self.order1.edited_by, self.user2)
        self.assertEqual(self.order1.package, self.package2)
        self.assertEqual(self.order1.first_name, 'Reza')

        # try without permission change_completed_order
        response = self.client.post(f'/admin/payment/order/{self.order2.pk}/change/', {
            'customer': self.user2.pk,
            'package': self.package1.pk,
            'first_name': 'Amir',
            'last_name': 'Red and Blue',
            'phone': '9304567890',
            'order_note': 'this can not change',
            'completed': True,
        })
        self.assertEqual(response.status_code, 403)

        # Granting permission to the staff user
        permission_for_change_completed_order = Permission.objects.get(codename='change_completed_order',
                                                                       content_type__app_label='payment')
        self.user2.user_permissions.add(permission_for_change_completed_order)

        # try with permission change_completed_order but with completed = True
        response = self.client.post(f'/admin/payment/order/{self.order2.pk}/change/', {
            'customer': self.user2.pk,
            'package': self.package1.pk,
            'first_name': 'Amir',
            'last_name': 'Red and Blue',
            'phone': '9304567890',
            'order_note': 'this can not change yet for completed=True',
            'completed': True,
        })
        self.assertEqual(response.status_code, 302)

        self.order2.refresh_from_db()
        self.assertTrue(self.order2.completed)
        self.assertNotEqual(self.order2.package, self.package1)
        self.assertNotEqual(self.order2.first_name, 'Amir')

        # try with permission change_completed_order and completed = False
        response = self.client.post(f'/admin/payment/order/{self.order2.pk}/change/', {
            'customer': self.user2.pk,
            'package': self.package1.pk,
            'first_name': 'Amir',
            'last_name': 'Red and Blue',
            'phone': '9304567890',
            'order_note': 'now this can change',
            'completed': False,
        })
        self.assertEqual(response.status_code, 302)

        self.order2.refresh_from_db()
        self.assertFalse(self.order2.completed)
        self.assertEqual(self.order2.uncompleted_by, self.user2)
        self.assertEqual(self.order2.edited_by, self.user2)
        self.assertEqual(self.order2.package, self.package1)
        self.assertEqual(self.order2.first_name, 'Amir')

    def test_delete_order(self):
        # order can not delete
        response = self.client.get(f'/admin/payment/order/{self.order1.pk}/delete/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/admin/payment/order/{self.order1.pk}/delete/', {
            'post': 'yes'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            order = Order.objects.get(pk=self.order1.pk)
        except Order.DoesNotExist:
            order = None
        self.assertIsNotNone(order, f"Order with pk {self.order1.pk} does not exist")

        # login in with staff user
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})

        response = self.client.post(f'/admin/payment/order/{self.package2.pk}/delete/', {
            'post': 'yes'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            order = Order.objects.get(pk=self.order2.pk)
        except Order.DoesNotExist:
            order = None
        self.assertIsNotNone(order, f"Order with pk {self.order2.pk} does not exist")

        permission_for_change_completed_order = Permission.objects.get(codename='change_completed_order',
                                                                       content_type__app_label='payment')
        self.user2.user_permissions.add(permission_for_change_completed_order)

        response = self.client.post(f'/admin/payment/order/{self.package2.pk}/delete/', {
            'post': 'yes'
        }, follow=True)
        self.assertEqual(response.status_code, 200)

        try:
            order = Order.objects.get(pk=self.order2.pk)
        except Order.DoesNotExist:
            order = None
        self.assertIsNotNone(order, f"Order with pk {self.order2.pk} does not exist")


