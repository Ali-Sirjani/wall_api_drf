from django.test import TestCase
from django import db
from django.conf import settings
from django.shortcuts import reverse
from django.utils import timezone
from django.utils.functional import SimpleLazyObject

from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from .models import CustomUser


class TestLogin(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user1 = CustomUser.objects.create_user(phone='09323744991')
        cls.user2 = CustomUser.objects.create_user(phone='09323744992', username='ALI')
        cls.user3 = CustomUser.objects.create_superuser(username='a', password='1')

    # CustomUser
    def test_info_user(self):
        # user1 with phone_number
        self.assertEqual(self.user1.phone_number.as_e164, '+989323744991')
        self.assertEqual(self.user1.username, '+989323744991')
        self.assertFalse(self.user1.has_usable_password(), False)
        self.assertEqual(self.user1.ad_token, 0)
        # user2 with phone_number and username
        self.assertEqual(self.user2.username, 'ALI')
        self.assertFalse(self.user2.has_usable_password(), False)
        self.assertEqual(self.user2.ad_token, 0)
        # user3 is superuser with username and password
        self.assertEqual(self.user3.username, 'a')
        self.assertEqual(self.user3.check_password('1'), True)
        self.assertEqual(self.user3.phone_number, None)
        self.assertEqual(self.user3.ad_token, 0)

    def test_unique_user_phone_number(self):
        self.user2.phone_number = '09323744991'
        try:
            self.user2.save()
            self.fail('phone_number is not unique!')
        except db.utils.IntegrityError:
            pass

    def test_unique_user_username(self):
        self.user2.username = '+989323744991'
        try:
            self.user2.save()
            self.fail('username is not unique!')
        except db.utils.IntegrityError:
            pass

    # CodeVarify
    def test_info_code_varify(self):
        code_varify1 = self.user1.codeverify
        code_varify3 = self.user3.codeverify
        # user1 normal user
        self.assertEqual(code_varify1.code, 0)
        self.assertEqual(code_varify1.expiration_timestamp, None)
        self.assertEqual(code_varify1.count_otp, 1)
        self.assertEqual(code_varify1.limit_time, None)
        # user3 super user
        self.assertEqual(code_varify3.code, 0)
        self.assertEqual(code_varify3.expiration_timestamp, None)
        self.assertEqual(code_varify3.count_otp, 1)
        self.assertEqual(code_varify3.limit_time, None)

    def test_check_code_without_generate_code_and_invalid_pk(self):
        # try with valid pk but without generate code
        session = self.client.session
        session['pk'] = '1'
        session.save()
        response = self.client.get(reverse('accounts:check_code'))
        self.assertEqual(self.client.session['pk'], '1')
        self.assertRedirects(response, reverse('accounts:login'))

        # try with invalid pk
        session['pk'] = '10'
        session.save()
        response = self.client.get(reverse('accounts:check_code'))
        self.assertEqual(self.client.session['pk'], '10')
        self.assertRedirects(response, reverse('accounts:login'))

    def test_login_with_phone_number_exists_account(self):
        response = self.client.post(reverse('accounts:login'), {'phone_number': '09323744991'})
        self.assertEqual(response.status_code, 302)

        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        code = code_varify1.code
        # send again
        for _ in range(settings.MAX_OTP_TRY - 2):
            response = self.client.get(reverse('accounts:check_code') + '?send_again=True')
            self.assertEqual(response.status_code, 302)
            code_varify1.refresh_from_db()
            self.assertEqual(code_varify1.code, code)
            self.assertEqual(code_varify1.limit_time, None)

        self.client.get(reverse('accounts:check_code') + '?send_again=True')
        code_varify1.refresh_from_db()
        self.assertIsNotNone(code_varify1.limit_time)

        # finish limit_time and expiration_timestamp
        code_varify1.limit_time -= timezone.timedelta(minutes=1)
        code_varify1.expiration_timestamp -= timezone.timedelta(minutes=2)
        code_varify1.save()

        self.client.get(reverse('accounts:check_code') + '?send_again=True')
        code_varify1.refresh_from_db()
        self.assertNotEqual(code_varify1.code, code)
        self.assertNotEqual(code_varify1.limit_time, None)

        # send code incorrectly
        response = self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code + 1})
        self.assertTrue(isinstance(response.wsgi_request.user, SimpleLazyObject))
        self.assertEqual(response.status_code, 200)

        # send code correctly
        response = self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code})
        self.assertTrue(isinstance(response.wsgi_request.user, CustomUser))
        self.assertRedirects(response, reverse('home'))

    def test_account_info_new_user(self):
        response = self.client.post(reverse('accounts:login'), {'phone_number': '09323744993'})
        self.assertEqual(len(CustomUser.objects.all()), 4)
        user4 = CustomUser.objects.last()
        self.assertEqual(user4.phone_number.as_e164, '+989323744993')
        self.assertEqual(user4.username, '+989323744993')
        self.assertFalse(user4.has_usable_password())

    def test_login_with_username_for_admin(self):
        # try login in with normal user
        response = self.client.post('/admin/login/', {
            'username': '09300644991',
            'password': '1'
        })
        self.assertEqual(response.status_code, 200)
        # try to enter the admin panel of site
        response = self.client.get('/admin/')
        self.assertRedirects(response, '/admin/login/?next=/admin/')

        # try login in with staff user
        self.client.post('/admin/login/', {
            'username': 'a',
            'password': '1'
        })
        # try to enter the admin panel of site
        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)

    def test_login_failed_with_django_axes(self):
        self.client.post(reverse('accounts:login'), {'phone_number': '09323744991'})
        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()

        for _ in range(settings.AXES_FAILURE_LIMIT):
            self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code + 1})

        response = self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code + 1})
        self.assertRedirects(response, reverse('accounts:login'))


class TestLoginAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        # user pk will start from 5
        cls.user1 = CustomUser.objects.create_user(phone='09315479800')
        cls.user2 = CustomUser.objects.create_user(phone='09315479801', username='reza')
        cls.user3 = CustomUser.objects.create_superuser(username='8001', password='q1w2')

    def test_generate_verification_code_with_phone_number(self):
        # first request for generating code
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get('user_id'), self.user1.pk)
        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.count_otp, 2)

        # second request for generating code but code must not send
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get('user_id'), self.user1.pk)
        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.count_otp, 2)

        # finish expire time
        code_varify1.expiration_timestamp -= timezone.timedelta(minutes=2)
        code_varify1.save()

        code = code_varify1.code
        # third request for generating code with expired code
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.assertEqual(response.data.get('user_id'), self.user1.pk)
        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.count_otp, 3)
        self.assertNotEqual(code_varify1.code, code)

    def test_confirm_code(self):
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        code_varify1 = self.user1.codeverify
        code = code_varify1.code

        # Count_otp has been increased due to the previous code generation request
        for _ in range(settings.MAX_OTP_TRY - 1):
            response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'send_again': True})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('send again'), 'Done')
        code_varify1.refresh_from_db()
        self.assertNotEqual(code_varify1.code, code)

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'send_again': True})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('times'), 'max otp try')

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'code': code_varify1.code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_refresh = response.data.get('refresh_token')
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.code, 0)

        response = self.client.post(reverse('accounts:token_refresh'), {'refresh': token_refresh})
        self.assertNotEqual(response.data.get('access'), None)

    def test_send_user_id_without_generate_code_or_invalid_pk(self):
        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('user_id'), 'user id is invalid')

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('authentication'), 'user did not create a code.')

    def test_user_info_api(self):
        # get token and test access token
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': self.user2.phone_number})
        self.user2.codeverify.refresh_from_db()
        response = self.client.post(reverse('accounts:check_code_api'), {
            'user_id': self.user2.pk,
            'code': self.user2.codeverify.code,
        })
        access_token_user2 = response.data.get('access_token')

        response = self.client.get(reverse('accounts:profile_api'),
                                   HTTP_AUTHORIZATION=f'Bearer {access_token_user2}')
        self.assertEqual(response.data.get('username'), self.user2.username)
        self.assertEqual(len(response.data), 10)

    def test_edit_user_info_api(self):
        access_token_user1 = RefreshToken.for_user(self.user1).access_token

        # try edit user1 info with token user1, without no data
        response = self.client.put(reverse('accounts:profile_edit_api'),
                                   HTTP_AUTHORIZATION=f'Bearer {access_token_user1}', content_type='application/json')
        self.assertEqual(response.data.get('message'), 'You must enter at least one field')

        # try edit user1 info with token user1, with data
        self.assertEqual(self.user1.username, '+989315479800')
        response = self.client.put(reverse('accounts:profile_edit_api'), {'username': 'test'},
                                   HTTP_AUTHORIZATION=f'Bearer {access_token_user1}', content_type='application/json')
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'test')

    def test_login_api_failed_with_django_axes(self):
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()

        for _ in range(settings.AXES_FAILURE_LIMIT):
            response = self.client.post(reverse('accounts:check_code_api'),
                                        {'user_id': self.user1.pk, 'code': code_varify1.code + 1})

        response = self.client.post(reverse('accounts:check_code_api'),
                                    {'user_id': self.user1.pk, 'code': code_varify1.code + 1})
        self.assertEqual(response.status_code, 403)
