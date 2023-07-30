from rest_framework import status
from rest_framework.response import Response

from accounts.serializers import CodeVarifySerializer


def phone_number_verification(request):
    user = request.user
    request.data['user_id'] = user.pk

    ser = CodeVarifySerializer(data=request.data)
    if ser.is_valid():
        code_varify = user.codeverify
        if code_varify.expiration_timestamp is not None:
            send_again = ser.validated_data.get('send_again')
            if send_again:
                if code_varify.send_code():
                    # send code to phone in request
                    print('this is code: ', code_varify.code)

                    return Response({'send again': 'Done'}, status=status.HTTP_200_OK)

                else:
                    return Response({'times': 'max otp try'}, status=status.HTTP_400_BAD_REQUEST)

            code = ser.validated_data.get('code')

            if code is None:
                return Response({'code': 'is empty'}, status=status.HTTP_400_BAD_REQUEST)

            if code_varify.code == code:
                if not code_varify.is_expired():
                    code_varify.reset()
                    return True

                return Response({'code': 'code has expired'}, status=status.HTTP_400_BAD_REQUEST)

            return Response({'code': 'wrong code'}, status=status.HTTP_400_BAD_REQUEST)

        if code_varify.send_code():
            code_varify.create_code()

            # send code to phone in request
            print('this is code: ', code_varify.code)

            return Response({'code': 'send'}, status=status.HTTP_200_OK)

    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)
