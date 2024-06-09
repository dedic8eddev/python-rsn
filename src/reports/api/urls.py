from django.urls import path
from reports.api import views

urlpatterns = [
    path('reports/', views.CreateReportApiView.as_view(), name='create-report'),
    path('reports/<int:pk>', views.ReportDeleteApiView.as_view(), name='delete-report'),
    path('reports/choices/', views.ReportChoicesApiView.as_view(), name='report-choices'),
    path('reports/reviews/', views.ReportedReviewListApiView.as_view(), name='reported-reviews'),
    path('reports/comments/', views.ReportedCommentsListApiView.as_view(), name='reported-comments'),
    path('reports/events/', views.ReportedEventsListApiView.as_view(), name='reported-events'),
    path('reports/pictures/', views.ReportedPicturesListApiView.as_view(), name='reported-pictures'),
    path('reports/users/', views.ReportedUsersListApiView.as_view(), name='reported-users'),
    path('reports/venues/', views.ReportedVenuesListApiView.as_view(), name='reported-venues'),
    path('reports/venues/', views.ReportedVenuesListApiView.as_view(), name='reported-venues'),
]
