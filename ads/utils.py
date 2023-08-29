from django.utils import timezone
from django.conf import settings

from rest_framework import status
from rest_framework.response import Response

from accounts.serializers import CodeVarifySerializer


def phone_number_verification(request):
    user = request.user
    request.data['user_id'] = user.pk

    ser = CodeVarifySerializer(data=request.data)
    if ser.is_valid():
        code_varify = user.codeverify
        if code_varify.expiration_timestamp is not None and code_varify.code:
            reset_time = code_varify.expiration_timestamp + timezone.timedelta(minutes=1)
            if timezone.now() < reset_time:
                send_again = ser.validated_data.get('send_again')
                if send_again:
                    if code_varify.send_code():

                        if not settings.TESTING:
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

            else:
                code_varify.reset()

        if code_varify.send_code():
            code_varify.create_code()

            if not settings.TESTING:
                # send code to phone in request
                print('this is code: ', code_varify.code)

            return Response({'message': 'you must verification ad phone number', 'code': 'send'}, status=status.HTTP_200_OK)

        return Response({'times': 'max otp try'}, status=status.HTTP_400_BAD_REQUEST)

    return Response(ser.errors, status=status.HTTP_400_BAD_REQUEST)


def cancel_create(request):
    cancel = request.query_params.get('cancel')

    if cancel == 'True':
        code = request.user.codeverify.code
        if code != 0:
            request.user.codeverify.code = 0
            request.user.codeverify.save()
            return Response({'status': 'cancel'}, status=status.HTTP_200_OK)

        return Response(
            {'status': 'fail', 'message': 'You did not request for create a ad yet'},
            status=status.HTTP_400_BAD_REQUEST
        )

    return Response({'status': 'fail', 'message': 'send True for params cancel'}, status=status.HTTP_400_BAD_REQUEST)
