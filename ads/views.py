from django.db.models import Q

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from .serializers import AdListSerializer, AdDetailSerializer, AdCreateOrUpdateSerializer,\
    SearchSerializer, CategorySerializer
from .models import Ad, Category
from .permissions import IsAdOwner


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
    def post(self, request, pk):
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
        if pk:
            try:
                ad = Ad.active_objs.get(pk=pk)
            except Ad.DoesNotExist:
                return Response({'message: ': f'There is no ad with this pk {pk}'}, status=status.HTTP_400_BAD_REQUEST)

            ser = AdDetailSerializer(ad)
            return Response(ser.data, status=status.HTTP_200_OK)

        return Response({'message: ': 'Please send pk ad'}, status=status.HTTP_400_BAD_REQUEST)


class CreateAdAPI(APIView):
    permission_classes = (IsAuthenticated, )
    serializer_class = AdCreateOrUpdateSerializer
    parser_classes = (MultiPartParser, )

    def post(self, request):
        ser = AdCreateOrUpdateSerializer(data=request.data)

        if ser.is_valid():
            ser.validated_data['author'] = request.user
            ser.save()
            data = {
                'status': 'Wait for confirmation',
            }
            return Response(data, status=status.HTTP_200_OK)

        return Response(ser.errors, status.HTTP_400_BAD_REQUEST)


class UpdateAdAPI(APIView):
    permission_classes = (IsAuthenticated, IsAdOwner)
    serializer_class = AdCreateOrUpdateSerializer

    def put(self, request, pk):
        if pk:
            try:
                ad = Ad.objects.get(pk=pk)
            except Ad.DoesNotExist:
                return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

            self.check_object_permissions(request, ad)

            ser = AdCreateOrUpdateSerializer(ad, data=request.data, partial=True)

            if ser.is_valid():
                ser.save()
                return Response({'status': 'updated', 'message': 'Wait for confirmation'}, status=status.HTTP_200_OK)

            return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)

        return Response({'message': 'send pk in url'}, status=status.HTTP_400_BAD_REQUEST)


class DeleteAdAPI(APIView):
    permission_classes = (IsAuthenticated, IsAdOwner)

    def delete(self, request, pk):
        if pk:
            try:
                ad = Ad.objects.get(pk=pk)
            except Ad.DoesNotExist:
                return Response({'message': f'There is no Ad with this pk({pk})'}, status=status.HTTP_400_BAD_REQUEST)

            self.check_object_permissions(request, ad)

            ad.delete()

            return Response({'status': 'done'})

        return Response({'message': 'send pk in url'}, status=status.HTTP_400_BAD_REQUEST)
