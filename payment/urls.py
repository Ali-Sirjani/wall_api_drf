from django.urls import path

from . import views

app_name = 'payment'

urlpatterns = [
    path('package/list/', views.PackageAdTokenListAPI.as_view(), name='packages_list'),
]
