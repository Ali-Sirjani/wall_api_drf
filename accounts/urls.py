from django.urls import path

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'accounts'


urlpatterns = [
    path('signup/', views.SignUpView.as_view(), name='signup'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('login/check-code/', views.check_code_view, name='check_code'),
    path('logout/', views.LogoutView.as_view(), name='logout'),
    path('login/api/', views.LoginAPI.as_view(), name='token_obtain_pair'),
    path('login/check-code/api/', views.CheckCodeAPI.as_view(), name='check_code_api'),
    path('refresh/api/', TokenRefreshView.as_view(), name='token_refresh'),
]
