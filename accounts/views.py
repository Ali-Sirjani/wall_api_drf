from django.contrib.auth import login, authenticate, views as auth_views
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CodeVerifyForm
from .serializers import UserSerializer, LoginSerializer, CodeVarifySerializer


class SignUpView(generic.CreateView):
    form_class = CustomUserCreationForm
    template_name = 'registration/signup.html'
    success_url = reverse_lazy('accounts:login')

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


class LoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    model = CustomUser
    success_url = reverse_lazy('accounts:check_code')

    def form_valid(self, form):
        # Authenticate the user with the provided credentials
        phone_number = form.cleaned_data.get('phone_number')

        if phone_number:
            # Set the backend attribute on the user object
            try:
                # Log in the user
                # login(self.request, user, backend='accounts.backends.UsernameOrPhoneModelBackend')
                user = authenticate(self.request, phone_number=phone_number.as_e164)
                if user is not None:
                    self.request.session['pk'] = user.pk
                    user.codeverify.create_code()
                    return redirect(self.success_url)

            except CustomUser.DoesNotExist:
                pass

        form.add_error('phone_number', 'Invalid phone number.')

        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


def check_code_view(request):
    form = CodeVerifyForm(request.POST or None)
    pk = request.session.get('pk')

    if pk:
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Something went wrong. Please try again!')
            return redirect('accounts:login')

        code = user.codeverify.code
        if not request.POST:
            print('this is code: ', code)

        if form.is_valid():
            num = form.cleaned_data.get('code')

            if code == num:
                if not user.codeverify.is_expired():
                    login(request, user, backend='accounts.backends.UsernameOrPhoneModelBackend')
                    return redirect('home')
                else:
                    messages.error(request, 'The code has timed out!')
            else:
                messages.error(request, 'The code is incorrect!')

    else:
        messages.error(request, 'The pk user is incorrect!')
        return redirect('accounts:login')

    context = {'form': form, 'code_varify': user.codeverify}

    return render(request, 'accounts/code_varify.html', context)


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
