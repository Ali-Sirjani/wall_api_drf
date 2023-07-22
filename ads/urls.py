from django.urls import path

from . import views

app_name = 'ads'

urlpatterns = [
    path('list/', views.AdsListAPI.as_view(), name='ads_list_api'),
    path('search/', views.SearchAdAPI.as_view(), name='search_ads'),
    path('list/category/', views.CategoryListAPI.as_view(), name='categories_list'),
    path('category/<int:pk>/', views.AdsListWithCategoryAPI.as_view(), name='ads_list_with_category'),
    path('create/', views.CreateAdAPI.as_view(), name='create_ad_api'),
    path('<int:pk>/', views.AdDetailAPI.as_view(), name='ad_detail_api'),
    path('update/<int:pk>/', views.UpdateAdAPI.as_view(), name='update_ad_api'),
    path('delete/<int:pk>/', views.DeleteAdAPI.as_view(), name='delete_ad_api'),
]
