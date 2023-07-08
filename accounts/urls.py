from django.urls import path

from . import views

app_name = 'accounts'


urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/check-code/', views.check_code_view, name='check_code'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
]




