from django.shortcuts import reverse

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status

import requests
import json

from .models import PackageAdToken, Order
from .serializers import PackageAdTokenSerializer, OrderCreateOrUpdateSerializer, OrderReadSerializer
from .permissions import IsUserOrderOwner
from .zarinpal import zarin_errors


class PackageAdTokenListAPI(APIView):
    def get(self, request):
        packages_list = PackageAdToken.active_objs.all()

        ser = PackageAdTokenSerializer(packages_list, many=True)

        return Response(ser.data, status=status.HTTP_200_OK)


class OrderRegistrationAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            order = Order.objects.get(customer=request.user.pk, completed=False)
            return Response({'message': 'You have a open Order, please update your order update url',
                             'update url': request.build_absolute_uri(
                                 reverse('payment:update_order', args=[order.pk]))}, status=status.HTTP_403_FORBIDDEN)
        except Order.DoesNotExist:
            pass

        ser = OrderCreateOrUpdateSerializer(data=request.data)

        if ser.is_valid():
            ser.validated_data['customer'] = request.user
            ser.validated_data['created_by'] = request.user

            ser.save()

            return Response({'status': 'Done', 'order url': request.build_absolute_uri(
                reverse('payment:order_detail', args=[ser.instance.pk]))})

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class UserOrdersListAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        orders_list = Order.objects.filter(customer=request.user.pk).order_by('-datetime_ordered')

        ser = OrderReadSerializer(orders_list, many=True)

        return Response(ser.data, status=status.HTTP_200_OK)


class OrderDetailAPI(APIView):
    permission_classes = (IsAuthenticated, IsUserOrderOwner)

    def get(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'message': f'There is no order with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(request, order)

        ser = OrderReadSerializer(order)

        return Response(ser.data, status=status.HTTP_200_OK)


class UpdateOrderAPI(APIView):
    permission_classes = (IsAuthenticated, IsUserOrderOwner)

    def put(self, request, pk):
        try:
            order = Order.objects.get(pk=pk)
        except Order.DoesNotExist:
            return Response({'message': f'There is no order with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(request, order)

        ser = OrderCreateOrUpdateSerializer(order, data=request.data, partial=True)

        if ser.instance.completed:
            return Response({'message': 'You can not edit completed order'}, status=status.HTTP_400_BAD_REQUEST)

        if ser.is_valid():

            ser.save()

            return Response({'status': 'Done'}, status=status.HTTP_200_OK)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class SandBoxProcessPaymentAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        try:
            order = Order.objects.get(customer=request.user.pk, completed=False)
        except Order.DoesNotExist:
            return Response({'message': 'You must register your order first'})

        toman_total = order.calc_price()

        rial_total = toman_total * 10

        zarinpal_url = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentRequest.json'

        request_header = {
            'accept': 'application/json',
            'content-type': 'application/json',
        }

        request_data = {
            'MerchantID': 'test--' * 6,
            'Amount': rial_total,
            'Description': f'transaction id: {order.transaction}',
            'CallbackURL': request.build_absolute_uri(reverse('payment:sandbox_callback')),
        }

        res = requests.post(url=zarinpal_url, data=json.dumps(request_data), headers=request_header)
        data = res.json()
        authority = data.get('Authority')

        if 'errors' not in data or len(data['errors']) == 0:
            payment_gateway_url = f'https://sandbox.zarinpal.com/pg/StartPay/{authority}'
            return Response({'gateway url': payment_gateway_url}, status=status.HTTP_200_OK)
        else:
            return Response({'errors': data['errors']}, status=status.HTTP_400_BAD_REQUEST)


class SandBoxCallPaymentAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request):
        try:
            order = Order.objects.get(customer=request.user.pk, completed=False)
        except Order.DoesNotExist:
            return Response({'message': 'You must register your order first'})

        payment_authority = request.query_params.get('Authority')
        payment_status = request.query_params.get('Status')

        toman_total = order.calc_price()

        rial_total = toman_total * 10

        if payment_status == 'OK':
            request_header = {
                'accept': 'application/json',
                'content-type': 'application/json',
            }

            request_data = {
                'MerchantID': 'test--' * 6,
                'Amount': rial_total,
                'Authority': payment_authority,
            }

            zarinpal_url_varify = 'https://sandbox.zarinpal.com/pg/rest/WebGate/PaymentVerification.json'

            res = requests.post(url=zarinpal_url_varify, data=json.dumps(request_data), headers=request_header)
            data = res.json()

            payment_code = data['Status']

            if payment_code == 100:
                order.close_order()
                return Response({'status': 'Done', 'number of ad token bought': order.token_quantity})

            return Response({'message': zarin_errors(payment_code)})

        else:
            return Response({'status': 'Failed'})
