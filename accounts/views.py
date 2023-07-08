from django.contrib.auth import login, authenticate, views as auth_views
from django.views import generic
from django.urls import reverse_lazy
from django.shortcuts import redirect, render
from django.contrib import messages

from .models import CustomUser
from .forms import CustomUserCreationForm, CustomAuthenticationForm, CodeVerifyForm


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
        user = CustomUser.objects.get(pk=pk)
        code = user.codeverify.code
        print('this is time: ', user.codeverify.expiration_timestamp)
        if not request.POST:
            print('this is code: ', code)

        if form.is_valid():
            num = form.cleaned_data.get('code')

            if code == num:
                if not user.codeverify.is_expired():
                    user.codeverify.save()
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
