from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .serializers import AdListSerializer, AdDetailSerializer
from .models import Ad


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
