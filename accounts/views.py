from django.contrib.auth import login, authenticate, views as auth_views
from django.urls import reverse_lazy
from django.shortcuts import redirect, render, reverse
from django.contrib import messages

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import CustomUser
from .forms import CustomAuthenticationForm, CodeVerifyForm
from .serializers import LoginSerializer, CodeVarifySerializer


class LoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    model = CustomUser
    success_url = reverse_lazy('accounts:check_code')

    def form_valid(self, form):
        phone_number = form.cleaned_data.get('phone_number')

        if phone_number:
            user = authenticate(self.request, phone_number=phone_number.as_e164)

            if user is not None:
                code_varify = user.codeverify  # Retrieves the code verification instance for the user.
                if code_varify.send_code():
                    self.request.session['pk'] = user.pk

                    if (code_varify.expiration_timestamp is None) or (code_varify.is_expired()):
                        code_varify.create_code()  # Generates a new verification code.

                    # send code
                    print('this is code: ', code_varify.code)
                    return redirect(self.success_url)

                form.add_error(None, 'Please after 10 minutes try Again')

        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


def check_code_view(request):
    pk = request.session.get('pk')
    if pk:
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Something went wrong. Please try again!')
            return redirect('accounts:login')

        referer = request.META.get('HTTP_REFERER')
        allow_url = request.build_absolute_uri(reverse('accounts:login'))

        code_varify = user.codeverify

        if referer == allow_url or code_varify.expiration_timestamp is not None:
            form = CodeVerifyForm(request.POST or None)

            code = code_varify.code
            send_again = request.GET.get('send_again')
            if send_again == 'True':
                if code_varify.send_code(request):
                    # send code
                    print('this is code: ', code_varify.code)

                return redirect('accounts:check_code')

            if form.is_valid():
                num = form.cleaned_data.get('code')

                if code == num:
                    if not code_varify.is_expired():
                        if user.last_login is None:
                            messages.success(request, 'Welcome to our site.')
                        elif user.last_login_for_month():
                            messages.success(request, 'Welcome back to our site')

                        login(request, user, backend='accounts.backends.UsernameOrPhoneModelBackend')
                        code_varify.expiration_timestamp = None
                        code_varify.count_otp = 0
                        code_varify.save()
                        return redirect('home')
                    else:
                        messages.error(request, 'The code has timed out!')
                else:
                    messages.error(request, 'The code is incorrect!')

            context = {'form': form, 'code_varify': code_varify}

            return render(request, 'accounts/code_varify.html', context)

    messages.error(request, 'The information sent is incorrect, please try again!')

    return redirect('accounts:login')


class LogoutView(auth_views.LogoutView):
    pass


class LoginAPI(APIView):
    def post(self, request):
        ser = LoginSerializer(data=request.data)

        if ser.is_valid():
            phone_number = ser.validated_data.get('phone_number')

            user = authenticate(request.data, phone_number=phone_number.as_e164)
            if user:
                user.codeverify.create_code()
                print('this is code: ', user.codeverify.code)
                return Response({'user_id': user.pk}, status=status.HTTP_200_OK)

            ser._errors.update({'phone_number': 'there is no user with this phone number'})

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class CheckCodeAPI(APIView):
    def post(self, request):
        ser = CodeVarifySerializer(data=request.data)

        if ser.is_valid():
            user_id = ser.validated_data.get('user_id')
            try:
                user = CustomUser.objects.get(pk=user_id)
            except CustomUser.DoesNotExist:
                return Response({'user_id: ': 'user id is invalid'}, status=status.HTTP_400_BAD_REQUEST)

            code = ser.validated_data.get('code')

            if user.codeverify.code == code:
                if not user.codeverify.is_expired():
                    refresh = RefreshToken.for_user(user)
                    access_token = str(refresh.access_token)
                    refresh_token = str(refresh)
                    return Response({'access_token': access_token, 'refresh_token': refresh_token},
                                    status=status.HTTP_200_OK
                                    )
                else:
                    return Response({'code: ': 'code has expired'}, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({'code: ': 'wrong code'}, status=status.HTTP_400_BAD_REQUEST)
