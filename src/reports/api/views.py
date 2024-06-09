from django.db.models import Count
from rest_framework.authentication import SessionAuthentication
from rest_framework.generics import CreateAPIView, ListAPIView, DestroyAPIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from reports.models import ReportChoices, Report
from web.api_permissions import StaffUserPermission
from web.authentication import CustomTokenAuthentication
from .api_filters import DataTablesJSOrderingFilter, DataTablesJSSearchFilter
from .pagination import DataTablesJSPagination
from .serializers import ReportCreateSerializer, ReportedReviewSerializer, ReportToPostSerializer, \
    ReportToUserSerializer, ReportToVenueSerializer


class ReportChoicesApiView(APIView):
    """
    View to list choices report.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]

    def get(self, request):
        """
        Return a dict of choices report.
        """
        choices = dict(ReportChoices.choices)
        return Response(choices)


class CreateReportApiView(CreateAPIView):
    """
    View to create Report of object
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication]
    serializer_class = ReportCreateSerializer


# /api/reports/reviews/
class ReportedReviewListApiView(ListAPIView):
    """
    List of reported reviews to Venues. Reviews tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportedReviewSerializer
    queryset = Report.objects.filter(
        comments__place__isnull=False,
        comments__place__is_archived=False,
        reporter__is_archived=False
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date']
    search_fields = ['comments__description', 'comments__place__name',
                     'comments__author__username', 'comments__author__email', 'comments__author__full_name',
                     'reporter__email', 'reporter__username', 'reporter__full_name']
    pagination_class = DataTablesJSPagination


# /api/reports/comments/
class ReportedCommentsListApiView(ListAPIView):
    """
    List of reported Comments under posts. Comments tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportedReviewSerializer
    queryset = Report.objects.filter(
        comments__post__isnull=False,
        comments__post__is_archived=False,
        reporter__is_archived=False
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date']
    search_fields = ['comments__description', 'comments__post__title', 'comments__post__description',
                     'comments__author__username', 'comments__author__email', 'comments__author__full_name',
                     'reporter__email', 'reporter__username', 'reporter__full_name']
    pagination_class = DataTablesJSPagination


# /api/reports/events/
class ReportedEventsListApiView(ListAPIView):
    """
    List of reported Comments under events. Events tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportedReviewSerializer
    queryset = Report.objects.filter(
        comments__cal_event__isnull=False,
        comments__cal_event__is_archived=False,
        reporter__is_archived=False
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date']
    search_fields = ['comments__description', 'comments__cal_event__title',
                     'comments__author__username', 'comments__author__email', 'comments__author__full_name',
                     'reporter__email', 'reporter__username', 'reporter__full_name']
    pagination_class = DataTablesJSPagination


# /api/reports/pictures/
class ReportedPicturesListApiView(ListAPIView):
    """
    List of reported Posts. Pictures tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportToPostSerializer
    queryset = Report.objects.filter(
        posts__isnull=False,
        posts__is_archived=False,
        reporter__is_archived=False
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date']
    search_fields = ['posts__title', 'posts__description', 'posts__author__email',
                     'posts__author__username', 'posts__author__full_name',
                     'reporter__email', 'reporter__username', 'reporter__full_name']
    pagination_class = DataTablesJSPagination


# /api/reports/users/
class ReportedUsersListApiView(ListAPIView):
    """
    List of reported User. Users tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportToUserSerializer
    queryset = Report.objects.filter(
        report_user__isnull=False,
        report_user__is_archived=False,
        reporter__is_archived=False
    ).annotate(
        reports_count=Count('report_user__report_user')
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date', 'reports_count']
    search_fields = ['report_user__author__email',
                     'report_user__username', 'report_user__full_name',
                     'reporter__email', 'reporter__username', 'reporter__full_name']
    pagination_class = DataTablesJSPagination


# /api/reports/venues/
class ReportedVenuesListApiView(ListAPIView):
    """
    List of reported Venues. Venues tab in the CMS.
    """
    permission_classes = [IsAuthenticated]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    serializer_class = ReportToVenueSerializer
    queryset = Report.objects.filter(
        places__isnull=False,
        places__is_archived=False,
        reporter__is_archived=False
    ).annotate(
        reports_count=Count('places__reports')
    )
    filter_backends = [DataTablesJSOrderingFilter, DataTablesJSSearchFilter]
    ordering_fields = ['created_date', 'reports_count']
    search_fields = ['reporter__email', 'reporter__username', 'reporter__full_name', 'places__name']
    pagination_class = DataTablesJSPagination


# /api/reports/<int:pk>
class ReportDeleteApiView(DestroyAPIView):
    """
    Delete Report
    """
    permission_classes = [StaffUserPermission]
    authentication_classes = [CustomTokenAuthentication, SessionAuthentication]
    queryset = Report.objects.all()
