from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

from web.models import Post, Place, Winemaker, CmsAdminComment


class Command(BaseCommand):
    args = ""
    help = "copy wineposts.team_comments, winemakers.team_comments, " \
           "places.team_comments to the corresponding CmsAdminComment"

    def handle(self, *args, **options):
        # handle wineposts
        qs_wineposts = Post.objects.filter(
            type=10,
            team_comments__isnull=False
        ).exclude(team_comments='')
        for wpst in qs_wineposts:
            comment = CmsAdminComment(
                content_type=ContentType.objects.get(app_label='web',
                                                     model='post'),
                object_id=wpst.id,
                author=wpst.expert if wpst.expert
                else wpst.last_modifier if wpst.last_modifier
                else wpst.author,
                content=wpst.team_comments
            )
            comment.save()
            CmsAdminComment.objects.filter(id=comment.id).update(
                created=wpst.modified_time,
                last_updated=wpst.modified_time
            )

        self.stdout.write("Winemakers has been processed")

        # handle winemakers
        qs_winemakers = Winemaker.active.filter(
            team_comments__isnull=False
        ).exclude(team_comments='')
        for wmkr in qs_winemakers:
            comment = CmsAdminComment(
                content_type=ContentType.objects.get(app_label='web',
                                                     model='winemaker'),
                object_id=wmkr.id,
                author=wmkr.last_modifier if wmkr.last_modifier
                else wmkr.author,
                content=wmkr.team_comments
            )
            comment.save()
            CmsAdminComment.objects.filter(id=comment.id).update(
                created=wmkr.modified_time,
                last_updated=wmkr.modified_time
            )
        self.stdout.write("Winemakers has been processed")

        # handle places
        qs_places = Place.active.filter(
            team_comments__isnull=False
        ).exclude(team_comments='')
        for place in qs_places:
            comment = CmsAdminComment(
                content_type=ContentType.objects.get(app_label='web',
                                                     model='place'),
                object_id=place.id,
                author=place.expert if place.expert
                else place.last_modifier if place.last_modifier
                else place.author,
                content=place.team_comments
            )
            comment.save()
            CmsAdminComment.objects.filter(id=comment.id).update(
                created=place.modified_time,
                last_updated=place.modified_time
            )
        self.stdout.write("Places has been processed")
