from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser

from .serializers import AdListSerializer, AdDetailSerializer, AdCreateOrUpdateSerializer
from .models import Ad
from .permissions import IsAdOwner


class AdsListAPI(APIView):
    serializer_class = AdListSerializer

    def get(self, request):
        ads_list = Ad.active_objs.all().order_by('-datetime_modified')
        ser = AdListSerializer(ads_list, many=True)
        return Response(ser.data, status=status.HTTP_200_OK)


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
    serializer_classes = AdCreateOrUpdateSerializer
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
