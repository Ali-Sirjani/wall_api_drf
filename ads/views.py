from django.db.models import Q
from django.db.utils import IntegrityError

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from .serializers import AdListSerializer, AdDetailSerializer, AdCreateOrUpdateSerializer,\
    SearchSerializer, CategorySerializer, AdReportSerializer
from .models import Ad, Category
from .permissions import IsAdOwner
from .utils import phone_number_verification, cancel_create


class AdsListAPI(APIView):
    serializer_class = AdListSerializer

    def get(self, request):
        ads_list = Ad.active_objs.all().order_by('-datetime_modified')
        ser = AdListSerializer(ads_list, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)


class CategoryListAPI(APIView):
    serializer_class = CategorySerializer

    def get(self, request):
        categories_list = Category.objects.all()
        ser = CategorySerializer(categories_list, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)


class AdsListWithCategoryAPI(APIView):
    def get(self, request, pk):
        try:
            category = Category.objects.get(pk=pk)
        except Category.DoesNotExist:
            return Response({'message': f'There is no category with this pk({pk})'}, status.HTTP_400_BAD_REQUEST)

        ads_list = Ad.active_objs.filter(category=category)
        ser = AdListSerializer(ads_list, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)


class SearchAdAPI(APIView):
    serializer_class = SearchSerializer

    def post(self, request):
        ser_search = SearchSerializer(data=request.data)
        if ser_search.is_valid():
            q = ser_search.validated_data['q']
            ads_list = Ad.active_objs.filter(Q(title__icontains=q) | Q(text__icontains=q) |
                                             Q(category__name__icontains=q)).distinct('id')
            ser = AdListSerializer(ads_list, many=True)

            return Response(ser.data, status=status.HTTP_200_OK)

        return Response(ser_search.errors, status=status.HTTP_400_BAD_REQUEST)


class AdDetailAPI(APIView):
    serializer_class = AdDetailSerializer

    def get(self, request, pk):
        try:
            ad = Ad.active_objs.get(pk=pk)
        except Ad.DoesNotExist:
            return Response({'message': f'There is no ad with this pk {pk}'}, status=status.HTTP_400_BAD_REQUEST)

        ser = AdDetailSerializer(ad)
        return Response(ser.data, status=status.HTTP_200_OK)


class ReportAdAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def post(self, request, pk):
        try:
            ad = Ad.active_objs.get(pk=pk)
        except Ad.DoesNotExist:
            return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        ser = AdReportSerializer(data=request.data)

        if ser.is_valid():
            ser.validated_data['ad'] = ad
            ser.validated_data['user'] = request.user
            try:
                ser.save()
                ser.instance.ad.count_reports += 1
                ser.instance.ad.save()
                return Response({'message': 'Ad reported successfully.'}, status=status.HTTP_201_CREATED)
            except IntegrityError:
                return Response({'message': 'You have already reported this ad.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateAdAPI(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = AdCreateOrUpdateSerializer
    parser_classes = (MultiPartParser, )

    def post(self, request):
        user = request.user
        double_check = request.query_params.get('use')
        is_use_ad_token = False

        if user.has_free_ad_quota():
            can_create = True

        elif not double_check:
            return Response(
                {'message': 'You have reached your ad creation limit. for use ad token send use=True in params of url'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        elif not double_check == 'True':
            return Response(
                {'message': 'Send \'use\' like this use=True'}, status=status.HTTP_400_BAD_REQUEST)

        elif user.try_using_ad_token(double_check):
            can_create = True
            is_use_ad_token = True

        else:
            return Response({'message': 'you have not ad token'}, status=status.HTTP_400_BAD_REQUEST)

        if can_create:
            if request.query_params.get('cancel'):
                return cancel_create(request)

            ser = AdCreateOrUpdateSerializer(data=request.data)

            if ser.is_valid():
                user_phone_e164 = user.phone_number.as_e164
                if not ser.validated_data['phone'] == user_phone_e164:
                    result = phone_number_verification(request)

                    if result is not True:
                        return result

                ser.validated_data['author'] = user

                ser.save()

                if is_use_ad_token:
                    ser.validated_data['is_use_ad_token'] = True
                    request.user.token_activated = False
                    request.user.save()

                data = {
                    'status': 'Wait for confirmation',
                }
                return Response(data, status=status.HTTP_201_CREATED)

            return Response(ser.errors, status.HTTP_400_BAD_REQUEST)


class UpdateAdAPI(APIView):
    permission_classes = (IsAuthenticated, IsAdOwner)
    serializer_class = AdCreateOrUpdateSerializer

    def put(self, request, pk):
        if request.query_params.get('cancel'):
            return cancel_create(request)

        try:
            ad = Ad.objects.get(pk=pk, is_delete=False)
        except Ad.DoesNotExist:
            return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(request, ad)

        ser = AdCreateOrUpdateSerializer(ad, data=request.data, partial=True)

        if ser.is_valid():
            user_phone_e164 = request.user.phone_number.as_e164
            phone_validate = ser.validated_data['phone']
            if not (phone_validate == user_phone_e164) and not (phone_validate == ad.phone):
                result = phone_number_verification(request)

                if result is not True:
                    return result

            ser.save()
            return Response({'status': 'updated', 'message': 'Wait for confirmation'}, status=status.HTTP_200_OK)

        return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAdAPI(APIView):
    permission_classes = (IsAuthenticated, IsAdOwner)

    def delete(self, request, pk):
        try:
            ad = Ad.objects.get(pk=pk, is_delete=False)
        except Ad.DoesNotExist:
            return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        self.check_object_permissions(request, ad)

        ad.soft_delete('user')

        return Response({'status': 'done'})


class SignAdAPI(APIView):
    permission_classes = (IsAuthenticated, )

    def get(self, request, pk):
        try:
            ad = Ad.active_objs.get(pk=pk)
        except Ad.DoesNotExist:
            return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        if ad.sign.filter(pk=user.pk).exists():
            ad.sign.remove(user)
            return Response({'status': 'remove'})

        ad.sign.add(user)
        return Response({'status': 'add'})


class UserSignAdsListAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        ads = Ad.active_objs.filter(sign=request.user.pk)
        ser = AdListSerializer(ads, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)
