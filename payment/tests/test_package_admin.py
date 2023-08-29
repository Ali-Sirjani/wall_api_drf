from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.conf import settings

from payment.models import PackageAdToken


class PackageAdTokenAdminTest(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user_model().objects.create_superuser(username='superuser', password='admin')

        cls.user2 = get_user_model().objects.create_superuser(username='staff', password='staff')
        cls.user2.is_superuser = False
        permission_list = [
            Permission.objects.get(codename='add_packageadtoken', content_type__app_label='payment'),
            Permission.objects.get(codename='change_packageadtoken', content_type__app_label='payment'),
            Permission.objects.get(codename='delete_packageadtoken', content_type__app_label='payment'),
        ]
        cls.user2.user_permissions.add(*permission_list)
        cls.user2.save()

        cls.package1 = PackageAdToken.objects.create(name='Token 1', description='this is package Token 1',
                                                     price=20_000, token_quantity=2)
        cls.package2 = PackageAdToken.objects.create(name='Token 2', description='this is package Token 2',
                                                     price=40_000, discount=True, discount_price=38_000,
                                                     token_quantity=4)

    def setUp(self):
        self.client.post('/admin/login/', {'username': 'superuser', 'password': 'admin'})

    def test_list_display(self):
        response = self.client.get('/admin/payment/packageadtoken/')
        self.assertContains(response, 'Name')
        self.assertContains(response, 'Price')
        self.assertContains(response, 'Discount price')
        self.assertContains(response, 'Token quantity')
        self.assertContains(response, 'Datetime modified')
        self.assertContains(response, 'Confirmation')
        self.assertContains(response, 'Is delete')

    def test_ordering(self):
        response = self.client.get('/admin/payment/packageadtoken/')
        packages = response.context['cl'].queryset
        self.assertEqual(packages.first(), self.package2)
        self.assertEqual(packages[1], self.package1)

        response = self.client.get('/admin/payment/packageadtoken/?o=4')
        packages = response.context['cl'].queryset
        self.assertEqual(packages.first(), self.package1)

    def test_list_filter(self):
        response = self.client.get('/admin/payment/packageadtoken/')
        self.assertContains(response, 'confirmation')
        self.assertContains(response, 'is delete')

        response = self.client.get('/admin/payment/packageadtoken/?confirmation__exact=1&o=2.-4')
        packages = response.context['cl'].queryset
        self.assertFalse(packages.exists())

        self.package1.confirmation = True

        response = self.client.get('/admin/payment/packageadtoken/?confirmation__exact=1&o=2.-4')
        packages = response.context['cl'].queryset
        self.assertFalse(packages.first(), self.package1)

        response = self.client.get('/admin/payment/packageadtoken/?confirmation__exact=1&is_delete__exact=1&o=2.-4')
        packages = response.context['cl'].queryset
        self.assertFalse(packages.exists())

    def test_create_package(self):
        # create with superuser.
        # superuser can change confirmation
        response = self.client.get('/admin/payment/packageadtoken/add/')
        self.assertEqual(response.status_code, 200)
        self.client.post('/admin/payment/packageadtoken/add/', {
            'name': 'New Token',
            'description': 'a good package',
            'token_quantity': 5,
            'confirmation': True,
        })

        new_token1 = PackageAdToken.objects.get(name='New Token')
        self.assertEqual(new_token1.price, 5 * settings.AD_TOKEN_PRICE)
        self.assertTrue(new_token1.confirmation)

        # create with staff user
        # confirmation always be False
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})
        self.client.post('/admin/payment/packageadtoken/add/', {
            'name': 'New Token 2',
            'description': 'a good package 2',
            'token_quantity': 6,
            'confirmation': True,

        })

        new_token2 = PackageAdToken.objects.get(name='New Token 2')
        self.assertEqual(new_token2.created_by.username, self.user2.username)
        self.assertEqual(new_token2.price, 6 * settings.AD_TOKEN_PRICE)
        self.assertFalse(new_token2.confirmation)

    def test_change_package(self):
        # just send the discount
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'Token 1',
            'description': 'this is package Token 1',
            'token_quantity': 2,
            'discount': True,
        })
        self.assertEqual(response.status_code, 200)
        # send just the discount_price
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'Token 1',
            'description': 'this is package Token 1',
            'token_quantity': 2,
            'discount_price': 10_000,
        })
        self.assertEqual(response.status_code, 200)
        # send the discount and the discount_price but discount > price
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'Token 1',
            'description': 'this is package Token 1',
            'token_quantity': 2,
            'discount': True,
            'discount_price': 30_000,
        })
        self.assertEqual(response.status_code, 200)
        # send the discount and the discount_price but discount == price
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'Token 1',
            'description': 'this is package Token 1',
            'token_quantity': 2,
            'discount': True,
            'discount_price': self.package1.price,
        })
        self.assertEqual(response.status_code, 200)
        # send the discount and the discount_price but discount < min_discount_price
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'Token 1',
            'description': 'this is package Token 1',
            'token_quantity': 2,
            'discount': True,
            'discount_price': 500,
        })
        self.assertEqual(response.status_code, 200)

        # send all fields with superuser
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'change Token 1',
            'description': 'change Token 1 with superuser',
            'discount': True,
            'token_quantity': 8,
            'discount_price': 40_000,
            'confirmation': True,
        })
        self.assertEqual(response.status_code, 302)

        self.package1.refresh_from_db()
        self.assertEqual(self.package1.name, 'change Token 1')
        self.assertEqual(self.package1.description, 'change Token 1 with superuser')
        self.assertTrue(self.package1.discount)
        self.assertEqual(self.package1.discount_price, 40_000)
        self.assertEqual(self.package1.token_quantity, 8)
        self.assertEqual(self.package1.price, 8 * settings.AD_TOKEN_PRICE)
        self.assertTrue(self.package1.confirmation)
        self.assertEqual(self.package1.edited_by.username, self.user1.username)

        # send without different values but with staff user.
        # confirmation must not change because the values of fields stay same
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'change Token 1',
            'description': 'change Token 1 with superuser',
            'discount': True,
            'token_quantity': 8,
            'discount_price': 40_000,
            'confirmation': True,
        })
        self.assertEqual(response.status_code, 302)

        self.assertTrue(self.package1.confirmation)

        # send with different values with staff user.
        # confirmation must change to False
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'change Token 1',
            'description': 'change Token 1 with staff user',
            'token_quantity': 8,
            'confirmation': True,
        })
        self.assertEqual(response.status_code, 302)

        self.package1.refresh_from_db()
        self.assertFalse(self.package1.discount)
        self.assertIsNone(self.package1.discount_price)
        self.assertEqual(self.package1.edited_by.username, self.user2.username)
        self.assertFalse(self.package1.confirmation)

    def test_soft_delete_and_undelete(self):
        # with superuser can change is_delete
        response = self.client.get(f'/admin/payment/packageadtoken/{self.package1.pk}/delete/')
        self.assertEqual(response.status_code, 200)

        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/delete/', {
            'post': 'yes'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.package1.refresh_from_db()
        self.assertTrue(self.package1.is_delete)

        response = self.client.post(f'/admin/payment/packageadtoken/{self.package1.pk}/change/', {
            'name': 'change',
            'description': 'can not change for is_delete=True'
        })
        self.assertEqual(response.status_code, 200)
        self.package1.refresh_from_db()
        self.assertNotEqual(self.package1.name, 'change')
        self.assertNotEqual(self.package1.description, 'can not change for is_delete=True')

        # with staff user can not change is_delete
        self.client.post('/admin/login/', {'username': self.user2.username, 'password': 'staff'})
        response = self.client.post(f'/admin/payment/packageadtoken/{self.package2.pk}/delete/', {
            'post': 'yes'
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.package1.refresh_from_db()
        self.assertFalse(self.package2.is_delete)
