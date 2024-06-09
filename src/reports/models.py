from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.utils.translation import gettext_lazy as _
from multiselectfield import MultiSelectField


class ReportChoices(models.TextChoices):
    SPAM = 'spam', _('Unwanted commercial content or spam')
    PORNOGRAPHY = 'pornography', _('Pornography or sexually explicit material')
    CHILD_ABUSE = 'child_abuse', _('Child abuse')
    HATE_SPEECH = 'hate_speech', _('Hate speech or graphic violence')
    TERRORISM = "terrorism", _('Promotes terrorism')
    BULLYING = 'bullying', _('Harassment or bullying')
    SUICIDE = 'suicide', _('Suicide or self injury')
    MISINFORMATION = 'misinformation', _('Misinformation')


class Report(models.Model):
    reporter = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE,
                                 null=True, blank=True, related_name='reporter')
    created_date = models.DateTimeField(auto_now_add=True)
    report = MultiSelectField(max_choices=8, choices=ReportChoices.choices, max_length=255, blank=True)
    last_editor = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE, null=True,
                                    blank=True, related_name='editor')
    edited_date = models.DateTimeField(auto_now=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField(null=True, blank=True)
    report_object = GenericForeignKey('content_type', 'object_id')
    report_user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE,
                                    null=True, blank=True, related_name='report_user')

    def __str__(self):
        return f'Report ID: {self.pk}'

    class Meta:
        ordering = ('created_date', )

    @property
    def report_app_label(self):
        return self.content_type.app_label

    @property
    def report_model(self):
        return self.content_type.model

    @property
    def author_reported_object(self):
        if hasattr(self.report_object, 'author'):
            return self.report_object.author
        return None

    @property
    def report_display(self):
        choices = dict(ReportChoices.choices)
        return [choices.get(report_key) for report_key in self.report]

    @property
    def comment(self):
        return self.comments.first()

    @property
    def post(self):
        return self.posts.first()

    @property
    def place(self):
        return self.places.first()


class BlockUser(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE,
                             related_name='blocker_user', null=True)
    block_user = models.ForeignKey(settings.AUTH_USER_MODEL, db_index=True, on_delete=models.CASCADE,
                                   related_name='blocked_user', null=True)
    blocked_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'block_user')
