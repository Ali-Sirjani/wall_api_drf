from django.urls import path

from . import views

app_name = 'payment'

urlpatterns = [
    path('package/list/', views.PackageAdTokenListAPI.as_view(), name='packages_list'),
    path('order/registration/', views.OrderRegistrationAPI.as_view(), name='order_registration'),
    path('order/list/', views.UserOrdersListAPI.as_view(), name='orders_list'),
    path('order/<int:pk>/', views.OrderDetailAPI.as_view(), name='order_detail'),
    path('order/update/<int:pk>/', views.UpdateOrderAPI.as_view(), name='update_order'),
]
