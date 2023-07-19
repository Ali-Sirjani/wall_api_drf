from django.urls import path

from . import views

app_name = 'ads'

urlpatterns = [
    path('list/', views.AdsListAPI.as_view(), name='ads_list_api'),
    path('create/', views.AdCreateAPI.as_view(), name='ad_create_api'),
    path('<int:pk>/', views.AdDetailAPI.as_view(), name='ad_detail_api'),
]
