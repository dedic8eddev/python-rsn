from django.db.models import Count, Q
from django.urls import reverse
from django.views.generic import TemplateView

from reports.models import Report, BlockUser
from web.views.admin.common import get_c


def get_counts():
    counts = Report.objects.aggregate(
        reported_reviews_count=Count('comments', filter=Q(comments__place__isnull=False)),
        reported_comments_count=Count('comments', filter=Q(comments__post__isnull=False)),
        reported_events_count=Count('comments', filter=Q(comments__cal_event__isnull=False)),
        reported_pictures_count=Count('posts'),
        reported_users_count=Count('report_user'),
        reported_venues_count=Count('places')
    )
    counts['blocked_users_count'] = BlockUser.objects.all().count()
    return counts


class ReportsView(TemplateView):
    template_name = 'reports/list/reports.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data()
        ctx['counts'] = get_counts()
        c = get_c(
            request=self.request, active='reports',
            path='/reports/', add_new_url=None
        )
        c['bc_path'] = [
            ('/', 'Home'),
            (reverse('reports'), 'Reported')
        ]
        return ctx
