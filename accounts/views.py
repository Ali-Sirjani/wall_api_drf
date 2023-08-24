from django.contrib.auth import login, authenticate, views as auth_views
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.shortcuts import redirect, render
from django.contrib import messages
from django.utils import timezone

from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated

from axes.decorators import axes_dispatch

from .models import CustomUser, CodeVerify
from .forms import CustomAuthenticationForm, CodeVerifyForm
from .serializers import LoginSerializer, CodeVarifySerializer, UserSerializer, UpdateUserSerializer
from .utils import signal_failed


class LoginView(auth_views.LoginView):
    form_class = CustomAuthenticationForm
    model = CustomUser
    success_url = reverse_lazy('accounts:check_code')

    def form_valid(self, form):
        phone_number = form.cleaned_data.get('phone_number')

        if phone_number:
            user = authenticate(self.request, phone_number=phone_number.as_e164)

            if user is not None:
                code_varify, created = CodeVerify.objects.get_or_create(user=user)

                if user.can_login():
                    if code_varify.can_start_again():
                        code_varify.reset()

                    self.request.session['pk'] = user.pk

                    if code_varify.code_time_validity():
                        if code_varify.send_code():
                            code_varify.create_code()  # Generates a new verification code.

                            # send code
                            print('this is code: ', code_varify.code)

                    return redirect(self.success_url)

                else:
                    form.add_error(None, 'You blocked because of too many login')

        return self.form_invalid(form)

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            return redirect('home')

        return super().dispatch(request, *args, **kwargs)


@axes_dispatch
def check_code_view(request):
    pk = request.session.get('pk')
    if pk:
        try:
            user = CustomUser.objects.get(pk=pk)
        except CustomUser.DoesNotExist:
            messages.error(request, 'Something went wrong. Please try again!')
            return redirect('accounts:login')

        code_varify, created = CodeVerify.objects.get_or_create(user=user)

        if code_varify.can_start_again():
            code_varify.reset()

        if code_varify.expiration_timestamp is not None:
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
                        del request.session['pk']

                        if user.last_login is None:
                            messages.success(request, 'Welcome to our site.')
                        elif user.last_login_for_month():
                            messages.success(request, 'Welcome back to our site')

                        login(request, user, backend='accounts.backends.UsernameOrPhoneModelBackend')
                        code_varify.reset()
                        user.can_login(True)
                        return redirect('home')
                    else:
                        messages.error(request, 'The code has timed out!')
                else:
                    signal_failed(request, user.phone_number)
                    messages.error(request, 'The code is incorrect!')

            context = {'form': form, 'code_varify': code_varify}

            return render(request, 'accounts/code_varify.html', context)

    messages.error(request, 'The information sent is incorrect, please try again!')

    return redirect('accounts:login')


class LogoutView(auth_views.LogoutView):

    def get(self, request):
        user = request.user
        if user.is_authenticated:
            code_varify, created = CodeVerify.objects.get_or_create(user=user)
            code_varify.reset()

        return super(LogoutView, self).get(request)


@method_decorator(axes_dispatch, name='dispatch')
class LoginAPI(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        ser = LoginSerializer(data=request.data)

        if ser.is_valid():
            phone_number = ser.validated_data.get('phone_number')

            user = authenticate(request, phone_number=phone_number.as_e164)
            if user:

                code_varify, created = CodeVerify.objects.get_or_create(user=user)
                if user.can_login():
                    if code_varify.can_start_again():
                        code_varify.reset()

                    if code_varify.code_time_validity():
                        if code_varify.send_code():
                            code_varify.create_code()

                            # send code
                            print('this is code: ', code_varify.code)

                    return Response({'user_id': user.pk}, status=status.HTTP_200_OK)

                return Response({'message': 'You limit for too many logout'})

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


@method_decorator(axes_dispatch, name='dispatch')
class CheckCodeAPI(APIView):
    serializer_class = CodeVarifySerializer

    def post(self, request):
        ser = CodeVarifySerializer(data=request.data)

        if ser.is_valid():
            user_id = ser.validated_data.get('user_id')
            try:
                user = CustomUser.objects.get(pk=user_id)
            except CustomUser.DoesNotExist:
                return Response({'user_id': 'user id is invalid'}, status=status.HTTP_400_BAD_REQUEST)

            code_varify, created = CodeVerify.objects.get_or_create(user=user)

            if code_varify.can_start_again():
                code_varify.reset()

            if code_varify.expiration_timestamp is not None:

                send_again = ser.validated_data.get('send_again')
                if send_again:
                    if code_varify.send_code():
                        # send code
                        print('this is code: ', code_varify.code)

                        return Response({'send again': 'Done'}, status=status.HTTP_200_OK)

                    else:
                        return Response({'times': 'max otp try'}, status=status.HTTP_400_BAD_REQUEST)

                code = ser.validated_data.get('code')

                if code_varify.code == code:
                    if not code_varify.is_expired():
                        user.can_login(True)

                        refresh = RefreshToken.for_user(user)
                        access_token = str(refresh.access_token)
                        refresh_token = str(refresh)

                        data = {'access_token': access_token, 'refresh_token': refresh_token}

                        if user.last_login is None:
                            data['message'] = 'Welcome to our site.'
                        elif user.last_login_for_month():
                            data['message'] = 'Welcome back to our site'

                        user.last_login = timezone.now()
                        user.save()

                        code_varify.reset()

                        return Response(data, status=status.HTTP_200_OK)

                    return Response({'code': 'code has expired'}, status=status.HTTP_400_BAD_REQUEST)

                signal_failed(request, user.phone_number)
                return Response({'code': 'wrong code'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'authentication': 'user did not create a code.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class UserInfoAPI(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = UserSerializer

    def get(self, request):
        ser = UserSerializer(request.user)
        return Response(ser.data, status=status.HTTP_200_OK)


class EditUserInfoAPI(APIView):
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserSerializer

    def put(self, request):
        ser = UpdateUserSerializer(request.user, data=request.data, partial=True)

        if ser.is_valid():
            if not len(ser.validated_data):
                return Response({'message': 'You must enter at least one field'},
                                status=status.HTTP_400_BAD_REQUEST)
            ser.save()
            return Response({'status': 'Done'}, status=status.HTTP_200_OK)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
