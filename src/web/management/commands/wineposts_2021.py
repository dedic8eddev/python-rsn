from django.core.management.base import BaseCommand

from web.management.commands import any_queryset_to_CSV
from web.models import Post


class Command(BaseCommand):
    args = ""
    help = "writes your QuerySet into CSV"

    def handle(self, *args, **options):
        qs = get_posts_qs()

        any_queryset_to_CSV.qs_to_local_csv(
            qs,
            fields=[
                'id',
                'created_time'
            ]
        )


def get_posts_qs():
    posts_qs = Post.objects.filter(created_time__year=2021, type=10)
    return posts_qs
