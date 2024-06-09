import logging

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.api.api_filters import DataTablesJSOrderingFilter, DataTablesJSSearchFilter
from reports.api.pagination import DataTablesJSPagination
from reports.api.serializers import BlockedUserSerializer
from reports.models import BlockUser
from web.authentication import CustomTokenAuthentication
from web.models import UserProfile
from web.serializers.users import BlockUserCreateSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication
from django.db.models import Count
from web.api_permissions import StaffUserPermission


log = logging.getLogger(__name__)


class UserDeleteAPIView(generics.DestroyAPIView):
    """
    delete user account + depersonalize all related data
    """

    authentication_classes = (CustomTokenAuthentication,)

    def get_object(self):
        user = self.request.user
        username = self.request.data.get('username')
        password = self.request.data.get('password')

        if (
                user.get_username() == username or user.email == username
        ) and user.check_password(raw_password=password):
            return user
        else:
            return None

    def destroy(self, request, *args, **kwargs):
        data = {}
        instance = self.get_object()
        if instance and instance.type == 40:
            data = {'message': 'You are trying to delete an OWNER'}
            return Response(status=status.HTTP_409_CONFLICT, data=data)
        elif instance and instance.type != 10:
            data = {'message': 'You are trying to delete not USER'}
            return Response(status=status.HTTP_409_CONFLICT, data=data)
        elif instance:
            self.perform_destroy(instance)
            return Response(status=status.HTTP_204_NO_CONTENT)
        else:
            data = {'message': 'Credentials are wrong or not provided'}
            return Response(status=status.HTTP_400_BAD_REQUEST, data=data)

    @swagger_auto_schema(
        operation_summary='Delete user',
        operation_description='Delete a user account for the request.user '
                              '+ depersonalize all related data'
    )
    def delete(self, request, *args, **kwargs):
        log.info('User %s requests self deletion.' % (
            self.request.user.username))
        return self.destroy(request, *args, **kwargs)


# /api/users/block
class UserBlockApiView(generics.CreateAPIView):
    """
    Block user per User for UGC
    """
    authentication_classes = (CustomTokenAuthentication,)
    serializer_class = BlockUserCreateSerializer


# /api/users/block/
class BlockedUserApiListView(generics.ListAPIView):
    """
    List of Blocked Users. Blocked User tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = BlockedUserSerializer
    queryset = BlockUser.objects.filter(user__is_archived=False, block_user__is_archived=False)\
        .annotate(blocks_count=Count('block_user__blocked_user'))
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['blocked_date', 'blocks_count']
    search_fields = ['user__email', 'user__username', 'user__full_name',
                     'block_user__email', 'block_user__username', 'block_user__full_name']
    pagination_class = DataTablesJSPagination


class BlockUserDeleteApiView(generics.DestroyAPIView):
    permission_classes = [StaffUserPermission]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    queryset = BlockUser.objects.all()


class AvailableUsernameAPIView(APIView):
    """
    Check the username for available
    """
    permission_classes = [AllowAny]

    def post(self, request):
        username_is_exist = UserProfile.objects.filter(username=request.data.get('query')).exists()
        if not username_is_exist:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_409_CONFLICT)


class AvailableEmailAPIView(APIView):
    """
    Check the email for available
    """
    permission_classes = [AllowAny]

    def post(self, request):
        email_is_exist = UserProfile.objects.filter(email=request.data.get('query')).exists()
        if not email_is_exist:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_409_CONFLICT)
