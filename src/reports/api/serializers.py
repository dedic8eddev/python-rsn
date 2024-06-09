from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from reports.models import Report, ReportChoices, BlockUser
from web.models import Place, Comment, Post, CalEvent


class ReportCreateSerializer(serializers.ModelSerializer):
    report = serializers.MultipleChoiceField(choices=ReportChoices.choices)
    report_app_label = serializers.CharField(required=True)
    report_model = serializers.CharField(required=True)
    created_date = serializers.DateTimeField(read_only=True)

    class Meta:
        model = Report
        fields = [
            'reporter',
            'report',
            'report_app_label',
            "report_model",
            'report_user',
            'object_id',
            'created_date',
            'report_display',
            'edited_date'
        ]

    def create(self, validated_data):
        request = self.context.get('request')
        reporter = request.user
        validated_data['reporter'] = reporter
        model = validated_data.pop('report_model')
        app_label = validated_data.pop('report_app_label')
        content_type = ContentType.objects.get(app_label=app_label, model=model)
        validated_data['content_type'] = content_type
        return Report.objects.create(**validated_data)


class ReporterSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            'id',
            'username',
            'absolute_url',
            'get_images',
            'status'
        ]


class ReportedVenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Place
        fields = [
            'id',
            'get_main_image',
            'name',
            'absolute_url',
        ]


class ReportedPostSerializer(serializers.ModelSerializer):
    author = ReporterSerializer(read_only=True)

    class Meta:
        model = Post
        fields = [
            'id',
            'author',
            'title',
            'description',
            'main_image_url',
            'absolute_url'
        ]


class ReportedCalEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = CalEvent
        fields = [
            'id',
            'title',
            'main_image_url',
            'absolute_url'
        ]


class ReportedCommentVenueSerializer(serializers.ModelSerializer):
    place = ReportedVenueSerializer(read_only=True)
    author = ReporterSerializer(read_only=True)
    post = ReportedPostSerializer(read_only=True)
    cal_event = ReportedCalEventSerializer(read_only=True)

    class Meta:
        model = Comment
        fields = [
            'id',
            'description',
            'author',
            'place',
            'post',
            'cal_event'
        ]


class ReportedReviewSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    comment = ReportedCommentVenueSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'report_display',
            'report',
            'created_date',
            'reporter',
            'comment'
        ]


class ReportToCommentSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    comment = ReportedCommentVenueSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            # 'id',
            'report_display',
            'report',
            'created_date',
            'reporter',
            'comment'
        ]


class ReportToPostSerializer(serializers.ModelSerializer):
    post = ReportedPostSerializer(read_only=True)
    reporter = ReporterSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'report_display',
            'report',
            'created_date',
            'reporter',
            'post'
        ]


class ReportToUserSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    report_user = ReporterSerializer(read_only=True)
    reports_count = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            'id',
            'created_date',
            'reporter',
            'report_display',
            'report_user',
            'report',
            'reports_count'
        ]

    def get_reports_count(self, obj):
        return obj.reports_count


class ReportToVenueSerializer(serializers.ModelSerializer):
    reporter = ReporterSerializer(read_only=True)
    reports_count = serializers.SerializerMethodField()
    place = ReportedVenueSerializer(read_only=True)

    class Meta:
        model = Report
        fields = [
            'id',
            'created_date',
            'reporter',
            'place',
            'report_display',
            'report',
            'reports_count',
        ]

    def get_reports_count(self, obj):
        return obj.reports_count


class BlockedUserSerializer(serializers.ModelSerializer):
    user = ReporterSerializer(read_only=True)
    block_user = ReporterSerializer(read_only=True)
    blocks_count = serializers.SerializerMethodField()

    class Meta:
        model = BlockUser
        fields = [
            'id',
            'blocked_date',
            'user',
            'block_user',
            'blocks_count'
        ]

    def get_blocks_count(self, obj):
        return obj.blocks_count
