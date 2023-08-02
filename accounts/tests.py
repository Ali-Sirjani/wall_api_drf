from django.test import TestCase
from django import db
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
        # user2 with phone_number and username
        self.assertEqual(self.user2.username, 'ALI')
        self.assertFalse(self.user2.has_usable_password(), False)
        # user3 is superuser with username and password
        self.assertEqual(self.user3.username, 'a')
        self.assertEqual(self.user3.check_password('1'), True)
        self.assertEqual(self.user3.phone_number, None)

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
        self.assertEqual(code_varify1.count_otp, 0)
        self.assertEqual(code_varify1.limit_time, None)
        # user3 super user
        self.assertEqual(code_varify3.code, 0)
        self.assertEqual(code_varify3.expiration_timestamp, None)
        self.assertEqual(code_varify3.count_otp, 0)
        self.assertEqual(code_varify3.limit_time, None)

    def test_login_with_phone_number_exists_account(self):
        session = self.client.session
        session['pk'] = '1'
        session.save()
        response = self.client.get(reverse('accounts:check_code'))
        self.assertEqual(self.client.session['pk'], '1')
        self.assertRedirects(response, reverse('accounts:login'))

        session['pk'] = '10'
        session.save()
        response = self.client.get(reverse('accounts:check_code'))
        self.assertEqual(self.client.session['pk'], '10')
        self.assertRedirects(response, reverse('accounts:login'))

        response = self.client.post(reverse('accounts:login'), {'phone_number': '09323744991'})
        self.assertEqual(response.status_code, 302)

        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        code = code_varify1.code
        # send again
        response = self.client.get(reverse('accounts:check_code') + '?send_again=True')
        self.assertEqual(response.status_code, 302)
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.code, code)
        self.assertEqual(code_varify1.limit_time, None)

        response = self.client.get(reverse('accounts:check_code') + '?send_again=True')
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.code, code)
        self.assertNotEqual(code_varify1.limit_time, None)

        code_varify1.limit_time -= timezone.timedelta(minutes=1)
        code_varify1.expiration_timestamp -= timezone.timedelta(minutes=2)
        code_varify1.save()

        response = self.client.get(reverse('accounts:check_code') + '?send_again=True')
        code_varify1.refresh_from_db()
        self.assertNotEqual(code_varify1.code, code)
        self.assertNotEqual(code_varify1.limit_time, None)

        response = self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code + 1})
        self.assertTrue(isinstance(response.wsgi_request.user, SimpleLazyObject))
        self.assertEqual(response.status_code, 200)

        response = self.client.post(reverse('accounts:check_code'), {'code': code_varify1.code})
        self.assertTrue(isinstance(response.wsgi_request.user, CustomUser))
        self.assertRedirects(response, reverse('home'))

    def test_login_with_phone_number_not_exists_account(self):
        response = self.client.post(reverse('accounts:login'), {'phone_number': '09323744993'})
        self.assertEqual(len(CustomUser.objects.all()), 4)
        user4 = CustomUser.objects.last()
        self.assertEqual(user4.phone_number.as_e164, '+989323744993')
        self.assertEqual(user4.username, '+989323744993')
        self.assertFalse(user4.has_usable_password(), False)

    def test_login_with_username_for_admin(self):
        response = self.client.post('/admin/login/', {
            'username': '09300644991',
            'password': '1'
        })
        self.assertEqual(response.status_code, 200)

        response = self.client.post('/admin/login/', {
            'username': 'a',
            'password': '1'
        })

        response = self.client.get('/admin/')
        self.assertEqual(response.status_code, 200)


class TestLoginAPI(TestCase):
    @classmethod
    def setUpTestData(cls):
        # user pk will start from 5
        cls.user1 = CustomUser.objects.create_user(phone='09315479800')
        cls.user2 = CustomUser.objects.create_user(phone='09315479801', username='reza')
        cls.user3 = CustomUser.objects.create_superuser(username='8001', password='q1w2')

    def test_take_token_with_phone_number(self):
        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 10})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('user_id'), 'user id is invalid')

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        print('this request : ', self.user1.pk)
        self.assertEqual(response.data.get('authentication'), 'user did not create a code.')

        for _ in range(3):
            response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('user_id'), self.user1.pk)

        response = self.client.post(reverse('accounts:login_api'), {'phone_number': '09315479800'})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('times'), 'max otp try')

        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        code_varify1.limit_time -= timezone.timedelta(minutes=1)
        code_varify1.save()

        for _ in range(4):
            response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'send_again': True})
            self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('send again'), 'Done')

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'send_again': True})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data.get('times'), 'max otp try')

        code_varify1 = self.user1.codeverify
        code_varify1.refresh_from_db()
        code_varify1.limit_time -= timezone.timedelta(minutes=1)
        code = code_varify1.code
        code_varify1.expiration_timestamp -= timezone.timedelta(minutes=2)
        code_varify1.save()

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'send_again': True})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data.get('send again'), 'Done')
        code_varify1.refresh_from_db()
        self.assertNotEqual(code_varify1.code, code)

        response = self.client.post(reverse('accounts:check_code_api'), {'user_id': 5, 'code': code_varify1.code})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        token_refresh = response.data.get('refresh_token')
        code_varify1.refresh_from_db()
        self.assertEqual(code_varify1.code, 0)

        response = self.client.post(reverse('accounts:token_refresh'), {'refresh': token_refresh})
        self.assertNotEqual(response.data.get('access'), None)

    def test_user_info_api(self):
        # get token and test access token
        response = self.client.post(reverse('accounts:login_api'), {'phone_number': self.user2.phone_number})
        self.user2.codeverify.refresh_from_db()
        response = self.client.post(reverse('accounts:check_code_api'), {
            'user_id': self.user2.pk,
            'code': self.user2.codeverify.code,
        })
        access_token_user2 = response.data.get('access_token')

        response = self.client.get(reverse('accounts:profile_api') + f'?pk={self.user2.pk}',
                                   HTTP_AUTHORIZATION=f'Bearer {access_token_user2}')
        self.assertEqual(response.data.get('username'), self.user2.username)
        self.assertEqual(len(response.data), 8)

        # get token
        access_token_user1 = RefreshToken.for_user(self.user1).access_token
        # try to access profile user2 with token user1
        response = self.client.get(reverse('accounts:profile_api') + f'?pk={self.user2.pk}',
                                   HTTP_AUTHORIZATION=f'Bearer {access_token_user1}')
        self.assertEqual(response.data.get('detail'), 'You do not have permission to perform this action.')

    def test_edit_user_info_api(self):
        access_token_user1 = RefreshToken.for_user(self.user1).access_token

        # try edit user2 info with token user1
        response = self.client.post(reverse('accounts:profile_edit_api') + f'?pk={self.user2.pk}', {'username': 'test'},
                                    HTTP_AUTHORIZATION=f'Bearer {access_token_user1}')
        self.assertEqual(response.data.get('detail'), 'You do not have permission to perform this action.')

        # try edit user1 info with token user1, without no data
        response = self.client.post(reverse('accounts:profile_edit_api') + f'?pk={self.user1.pk}',
                                    HTTP_AUTHORIZATION=f'Bearer {access_token_user1}')
        self.assertEqual(response.data.get('message'), 'You must enter at least one field')

        # try edit user1 info with token user1, with data
        self.assertEqual(self.user1.username, '+989315479800')
        response = self.client.post(reverse('accounts:profile_edit_api') + f'?pk={self.user1.pk}', {'username': 'test'},
                                    HTTP_AUTHORIZATION=f'Bearer {access_token_user1}')
        self.user1.refresh_from_db()
        self.assertEqual(self.user1.username, 'test')

