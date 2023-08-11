from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from .models import PackageAdToken
from .serializers import PackageAdTokenSerializer


class PackageAdTokenListAPI(APIView):
    def get(self, request):
        packages_list = PackageAdToken.active_objs.all()

        ser = PackageAdTokenSerializer(packages_list, many=True)

        return Response(ser.data, status=status.HTTP_200_OK)
