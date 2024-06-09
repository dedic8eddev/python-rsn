from rest_framework import serializers

from web.constants import MOBILE_DATE_FORMAT, PostStatusE, PostTypeE, AppEnvE
from web.models import Post, Wine
from web.serializers.places import FullPlaceSerializer
from web.serializers.utils import (BadgeExpiryDateMsField, HasBadgeDataField,
                                   ImageUrlField, MentionsField, ToReprMixin)
from web.serializers.winemakers import (LongWinemakerSerializer,
                                        ShortWinemakerSerializer)
from web.utils import api_blocked_users
from web.utils.model_app_legacy import (api_status_wine, api_status_winepost,
                                        api_status_winepost_tl)
from web.utils.model_tools import get_sulfur_levels_from_yearly_data, load_json
from web.utils.upload_tools import aws_url


class WinePostAPISerializer(serializers.ModelSerializer):
    venue_id = serializers.CharField(source="place_id")
    modified_time = serializers.CharField()  # legacy
    created_time = serializers.CharField()  # legacy

    price = serializers.FloatField()
    wine_kind = serializers.IntegerField(source='status')
    year = serializers.SerializerMethodField()
    is_sparkling = serializers.BooleanField(source='wine_is_sparkling')

    name = serializers.CharField(source="wine_name")
    name_short = serializers.CharField(source="wine_name")  # legacy
    color = serializers.CharField(source="wine_color")
    designation = serializers.CharField(source="wine_designation")
    domain = serializers.CharField(source="wine_domain")
    region = serializers.CharField(source="wine_region")

    similiar_wine_exists = serializers.BooleanField(
        source="wine_similiar_wine_exists"
    )  # typos are legacy
    similiar_wine_id = serializers.CharField(
        source="wine_similiar_wine_id"
    )  # typos are legacy
    status = serializers.IntegerField(source="wine_status")
    sulfur_levels = serializers.SerializerMethodField()

    author = serializers.CharField(source="wine_author_username")
    author_has_badge = HasBadgeDataField(source="wine_winemaker_author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="wine_winemaker_author")  # noqa

    main_image = serializers.SerializerMethodField()

    winemaker = serializers.SerializerMethodField()
    winemaker_id = serializers.CharField(source="wine_winemaker_identifier")
    winemaker_name = serializers.CharField(source="wine_winemaker_name")

    total_likevote_number = serializers.IntegerField(
        source="wine_likevote_number"
    )
    total_comment_number = serializers.IntegerField(
        source="wine_comment_number"
    )
    total_drank_it_too_number = serializers.IntegerField(
        source="wine_drank_it_too_number"
    )
    total_star_review_number = serializers.IntegerField(
        source="wine_total_star_review_number"
    )
    wine_post_number = serializers.IntegerField(
        source="wine_wine_post_number"
    )

    i_like_it = serializers.SerializerMethodField()
    i_drank_it_too = serializers.SerializerMethodField()

    def get_winemaker(self, obj):
        return LongWinemakerSerializer(obj.wine.winemaker).data

    def get_currency(self, obj):
        return str(obj.currency) if obj.currency else 'EUR'

    def get_sulfur_levels(self, obj):
        pp_yearly_data = load_json(
            obj.yearly_data
        ) if obj.yearly_data else None

        sulfur_levels = get_sulfur_levels_from_yearly_data(
            pp_yearly_data
        )

        return sulfur_levels

    def get_year(self, obj):
        wine_year = obj.wine_year

        return wine_year if wine_year and str(wine_year) != '0' else ""

    def get_main_image(self, obj):
        post_main_image = obj.main_image
        wine_main_image = obj.wine.main_image

        if post_main_image:
            return aws_url(post_main_image)

        if wine_main_image:
            return aws_url(wine_main_image)

        return None

    def get_i_like_it(self, obj):
        if (
            not self.context['request'] or
            not hasattr(self.context['request'], 'user') or
            self.context['request'].user.is_anonymous
        ):
            return False

        return obj.like_votes.filter(
            is_archived=False,
            author=self.context['request'].user
        ).exists()

    def get_i_drank_it_too(self, obj):
        if (
            not self.context['request'] or
            not hasattr(self.context['request'], 'user') or
            self.context['request'].user.is_anonymous
        ):
            return False

        return obj.drank_it_toos.filter(
            is_archived=False,
            author=self.context['request'].user
        ).exists()

    class Meta:
        model = Post
        fields = ['venue_id', 'wine_id', 'modified_time', 'created_time',
                  'certified_by', 'wine_trade', 'price', 'currency', 'id',
                  'title', 'grape_variety', 'wine_kind', 'free_so2',
                  'total_so2', 'year', 'is_archived', 'is_biodynamic',
                  'is_organic', 'is_sparkling', 'author', 'name', 'name_short',
                  'color', 'designation', 'domain', 'region',
                  'similiar_wine_exists', 'similiar_wine_id', 'status',
                  'author_has_badge', 'author_badge_expiry_date_ms',
                  'sulfur_levels', 'winemaker_id', 'winemaker_name',
                  'main_image', 'total_likevote_number',
                  'total_comment_number', 'total_drank_it_too_number',
                  'total_star_review_number', 'wine_post_number', 'winemaker',
                  'i_like_it', 'i_drank_it_too']


class MinimalWinePostAPISerializer(serializers.ModelSerializer):
    name_short = serializers.CharField(source="wine_name")  # legacy
    domain = serializers.CharField(source="wine_domain")
    main_image = serializers.SerializerMethodField()
    name = serializers.CharField(source="wine_name")
    wine_kind = serializers.IntegerField(source='status')

    def get_main_image(self, obj):
        post_main_image = obj.main_image
        wine_main_image = obj.wine.main_image

        if post_main_image:
            return aws_url(post_main_image)

        if wine_main_image:
            return aws_url(wine_main_image)

        return None

    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['winemaker'] = {'id': obj.wine.winemaker.id}

        return data

    class Meta:
        model = Post
        fields = ['name_short', 'domain', 'main_image', 'name', 'wine_kind']


class FoodPostAPISerializer(ToReprMixin, serializers.ModelSerializer):
    venue_id = serializers.CharField(source="place_identifier")
    post_id = serializers.CharField(source="id")
    post_kind = serializers.CharField(source='status')
    # legacy duplication
    post_status = serializers.CharField(source='status')
    status = serializers.IntegerField()

    modified_time = serializers.CharField()  # legacy
    created_time = serializers.CharField()  # legacy

    author = serializers.CharField(source='author.username')
    author_id = serializers.UUIDField(source="author.id")
    author_avatar_url = ImageUrlField(source='author.image')
    author_has_badge = HasBadgeDataField(source="wine_winemaker_author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="wine_winemaker_author")  # noqa

    post_main_image = ImageUrlField(source='main_image')

    in_doubt = serializers.SerializerMethodField()
    mentions = MentionsField(source="user_mentions")

    expert = serializers.CharField(source="expert_username")
    expert_id = serializers.UUIDField(source="expert_identifier")
    expert_avatar_url = ImageUrlField(source='expert_image')

    i_like_it = serializers.SerializerMethodField()

    def get_i_like_it(self, obj):
        if (
            not self.context['request'] or
            not hasattr(self.context['request'], 'user') or
            self.context['request'].user.is_anonymous
        ):
            return False

        return obj.like_votes.filter(
            is_archived=False,
            author=self.context['request'].user
        ).exists()

    def get_in_doubt(self, obj):
        return obj.status == PostStatusE.IN_DOUBT

    class Meta:
        model = Post
        fields = ['venue_id', 'author', 'author_id', 'author_avatar_url',
                  'author_has_badge', 'author_badge_expiry_date_ms',
                  'comment_number', 'description', 'drank_it_too_number', 'id',
                  'is_archived', 'likevote_number', 'post_id', 'post_kind',
                  'post_main_image', 'post_status', 'status', 'title', 'type',
                  'mentions', 'in_doubt', 'expert', 'expert_id',
                  'expert_avatar_url', 'created_time', 'modified_time',
                  'i_like_it']


class WineSerializer(ToReprMixin, serializers.ModelSerializer):
    # equivalent of to_dict
    # include_winemaker_data True by default
    author = serializers.CharField(source='author.username')
    author_has_badge = HasBadgeDataField(source="author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="author")  # noqa

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    main_image = serializers.SerializerMethodField()
    winemaker_name = serializers.CharField(source='winemaker_name_property')
    winemaker = serializers.SerializerMethodField()

    total_likevote_number = serializers.SerializerMethodField()
    total_comment_number = serializers.SerializerMethodField()
    total_drank_it_too_number = serializers.SerializerMethodField()
    wine_post_number = serializers.SerializerMethodField()
    total_star_review_number = serializers.SerializerMethodField()
    wine_trade = serializers.SerializerMethodField()

    def get_main_image(self, obj):
        return obj.get_main_image_url(
            fallback_parent_post_image=bool(
                self.context.get('fallback_parent_post_image')
            ),
            fallback_child_post_image=bool(
                self.context.get('fallback_child_post_image')
            )
        )

    def get_winemaker(self, obj):
        if (
            not self.context.get('include_winemaker_data') and
            not self.context.get('include_winemaker_basic_data') and
            not self.context.get('include_winemaker_minimal_data')
        ):
            return None

        if not obj.winemaker:
            return None

        if self.context.get('include_winemaker_data'):
            return LongWinemakerSerializer(obj.winemaker).data

        if self.context.get('include_winemaker_basic_data'):
            return ShortWinemakerSerializer(obj.winemaker).data

        if self.context.get('include_winemaker_minimal_data'):
            return {
                "domain": obj.winemaker.domain,
                "name": obj.winemaker.name
            }

    def get_total_likevote_number(self, obj):
        # except likes from blocked users
        return api_blocked_users.get_likevotes_number(self=self, obj=obj)

    def get_total_comment_number(self, obj):
        # except comments from blocked users
        return api_blocked_users.get_comments_number(self=self, obj=obj)

    def get_total_drank_it_too_number(self, obj):
        # except drank_it_toos from blocked users
        return api_blocked_users.get_drank_it_toos_number(self=self, obj=obj)

    def get_wine_post_number(self, obj):
        if hasattr(obj, 'wine_post_number_annotated'):
            return obj.wine_post_number_annotated
        return obj.posts.filter(
            type=PostTypeE.WINE, status=PostStatusE.PUBLISHED
        ).count()

    def get_total_star_review_number(self, obj):
        if hasattr(obj, 'total_star_review_number_annotated'):
            return obj.total_star_review_number_annotated
        return obj.posts.filter(
            type=PostTypeE.WINE, status=PostStatusE.PUBLISHED,
            is_star_review=True
        ).count()

    def get_wine_trade(self, obj):
        if hasattr(obj, 'wine_trade'):
            return obj.wine_trade

        pp = obj.posts.filter(type=PostTypeE.WINE, is_parent_post=True).first()

        if not pp:
            return None

        return pp.wine_trade

    class Meta:
        model = Wine
        fields = ['id', 'author', 'author_has_badge',
                  'author_badge_expiry_date_ms', 'created_time',
                  'modified_time', 'status', 'is_archived', 'name',
                  'name_short', 'domain', 'designation', 'grape_variety',
                  'region', 'color', 'year', 'is_sparkling', 'main_image',
                  'winemaker_id', 'winemaker_name', 'total_likevote_number',
                  'total_comment_number', 'total_drank_it_too_number',
                  'wine_post_number', 'total_star_review_number',
                  'similiar_wine_id', 'similiar_wine_exists', 'wine_trade',
                  'winemaker']


class FullWineSerializer(WineSerializer):
    # equivalent of to_dict_api
    # include_winemaker_data True by default
    def to_representation(self, obj):
        data = super().to_representation(obj)

        parent_post = Post.active.filter(wine=obj, is_parent_post=True).first()

        api_status_legacy_data = api_status_wine(
            parent_post
        ) if parent_post else api_status_wine(obj)

        data['status'] = api_status_legacy_data['status']
        data['wine_kind'] = api_status_legacy_data['wine_kind']

        if 'in_doubt' in api_status_legacy_data:
            data['in_doubt'] = api_status_legacy_data['in_doubt']

        if 'is_archived' in api_status_legacy_data:
            data['is_archived'] = api_status_legacy_data['is_archived']

        if parent_post:
            get_free_so2_data = parent_post.get_free_so2()
            data['free_so2'] = get_free_so2_data['free_so2']
            data['total_so2'] = get_free_so2_data['total_so2']
            data['grape_variety'] = get_free_so2_data['grape_variety']
            data['is_organic'] = parent_post.is_organic
            data['is_biodynamic'] = parent_post.is_biodynamic
            data['certified_by'] = parent_post.certified_by

            if parent_post.yearly_data:
                data['yearly_data'] = parent_post.yearly_data
                data['sulfur_levels'] = []

                for ppyd_year, ppyd_data in parent_post.yearly_data.items():
                    data['sulfur_levels'].append({
                        'year': int(ppyd_year) if ppyd_year.isdigit() else None,  # noqa
                        'free_so2': ppyd_data['free_so2'] if 'free_so2' in ppyd_data else None,  # noqa
                        'total_so2': ppyd_data['total_so2'] if 'total_so2' in ppyd_data else None,  # noqa
                        'grape_variety': ppyd_data['grape_variety'] if 'grape_variety' in ppyd_data else None,  # noqa
                    })

        if hasattr(obj, 'similarity'):
            data['similarity'] = obj.similarity

        return data


class WineWithYearSerializer(WineSerializer):
    # pass
    # equivalent of to_dict_api_year
    # include_winemaker_data True by default
    def to_representation(self, obj):
        data = super().to_representation(obj)
        data['year_vintage'] = data['year']
        del data['year']

        if hasattr(obj, 'parent_post_status'):
            parent_post = Post(status=obj.parent_post_status)
        else:
            parent_post = Post.active.filter(wine=obj, is_parent_post=True).first()

        api_status_legacy_data = api_status_wine(
            parent_post
        ) if parent_post else api_status_wine(obj)
        data['status'] = api_status_legacy_data['status']
        data['wine_kind'] = api_status_legacy_data['wine_kind']

        return data


class PostSerializer(ToReprMixin, serializers.ModelSerializer):
    # equivalent of old to_dict
    # old default was include_wine_data=True
    author = serializers.CharField(source='author.username')
    author_id = serializers.UUIDField(source="author.id")
    author_avatar_url = ImageUrlField(source='author.image')
    author_has_badge = HasBadgeDataField(source="wine_winemaker_author")
    author_badge_expiry_date_ms = BadgeExpiryDateMsField(source="wine_winemaker_author")  # noqa

    created_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)
    modified_time = serializers.DateTimeField(format=MOBILE_DATE_FORMAT)

    expert = serializers.CharField(source="expert_username")
    expert_id = serializers.UUIDField(source="expert_identifier")
    expert_avatar_url = ImageUrlField(source='expert_image')

    post_id = serializers.IntegerField(source="id")
    post_main_image = serializers.SerializerMethodField()
    wine_main_image = ImageUrlField(source='wine_main_image_property')
    wine_main_image_id = serializers.IntegerField(source='wine_main_image_identifier')
    wine_ref_image = ImageUrlField(source='wine_ref_image_property')
    wine_ref_image_id = serializers.IntegerField(source='wine_ref_image_identifier')

    vuf_rating_tracking = serializers.CharField(source="get_vuf_rating_tracking")  # noqa
    vuf_rating_reco = serializers.CharField(source="wine_ref_image_rating_reco")  # noqa

    vuf_match_post_status = serializers.CharField(source="vuf_match_post_status_property")  # noqa
    vuf_match_post_title = serializers.CharField(source="vuf_match_post_wine_name")  # noqa
    vuf_match_post_id = serializers.IntegerField()
    vuf_match_post_pp = serializers.BooleanField(source="vuf_match_post_is_parent_post")  # noqa

    vuf_match_post_ref_image = ImageUrlField(source='vuf_match_post_wine_ref_image')  # noqa
    vuf_match_post_ref_image_id = serializers.IntegerField(source="vuf_match_post_wine_ref_image_id")  # noqa
    vuf_match_rating_tracking = serializers.CharField(source="vuf_match_post_wine_ref_image_rating_tracking")  # noqa
    vuf_match_post_wm_natural = serializers.BooleanField(source="vuf_match_post_wine_winemaker_get_is_natural")  # noqa
    vuf_match_post_year = serializers.CharField(source="vuf_match_post_wine_year")  # noqa

    vuf_match_wine_name = serializers.CharField(source="vuf_match_wine_name_property") # noqa
    vuf_match_wine_id = serializers.CharField(source="vuf_match_wine_identifier") # noqa
    vuf_match_wine_status = serializers.CharField(source="vuf_match_wine_status_property")  # noqa
    vuf_match_wine_wm_natural = serializers.BooleanField(source="vuf_match_wine_winemaker_get_is_natural")  # noqa

    wm_natural = serializers.BooleanField(source="wine_winemaker_get_is_natural")  # noqa
    wine = serializers.CharField(source="wine_name")
    wine_id = serializers.CharField(source="wine_identifier")

    place_name = serializers.CharField(source="place_name_property")
    place_free_glass = serializers.BooleanField(source="place_free_glass_property") # noqa
    place_free_glass_signup_date = serializers.DateTimeField(source="place_free_glass_signup_date_property")  # noqa
    place_gfg_count = serializers.SerializerMethodField()
    place_i_got = serializers.SerializerMethodField()

    i_like_it = serializers.SerializerMethodField()
    i_drank_it_too = serializers.SerializerMethodField()

    likevote_number = serializers.SerializerMethodField()
    comment_number = serializers.SerializerMethodField()
    drank_it_too_number = serializers.SerializerMethodField()

    wine_data = serializers.SerializerMethodField()
    place_data = FullPlaceSerializer(source="place")

    post_status = serializers.IntegerField(source="status")
    in_doubt = serializers.BooleanField(source="get_in_doubt")
    mentions = MentionsField(source="user_mentions")

    currency = serializers.SerializerMethodField()

    def get_wine_data(self, obj):
        if (
            self.context.get('include_wine_data') and
            obj.type == PostTypeE.WINE
        ):
            return WineSerializer(obj.wine, context=self.context).data

        return None

    def get_post_main_image(self, obj):
        return obj.get_post_main_image_url(
            fallback_wine_image=bool(self.context.get('fallback_wine_image'))
        )

    def get_place_gfg_count(self, obj):
        if not obj.place:
            return 0

        return obj.place.got_free_glass_objects.filter(
            is_archived=False
        ).count()

    def get_place_i_got(self, obj):
        if not obj.place or not self.context['request'].user.is_authenticated:
            return 0

        return obj.place.got_free_glass_objects.filter(
            is_archived=False,
            author=self.context['request'].user
        ).count()

    def get_currency(self, obj):
        return obj.currency if obj.currency else 'EUR'

    def get_i_like_it(self, obj):
        if (
            not self.context['request'] or
            not hasattr(self.context['request'], 'user') or
            self.context['request'].user.is_anonymous
        ):
            return False

        return obj.like_votes.filter(
            is_archived=False,
            author=self.context['request'].user
        ).exists()

    def get_i_drank_it_too(self, obj):
        if (
            not self.context['request'] or
            not hasattr(self.context['request'], 'user') or
            self.context['request'].user.is_anonymous
        ):
            return False

        return obj.drank_it_toos.filter(
            is_archived=False,
            author=self.context['request'].user
        ).exists()

    def get_likevote_number(self, obj):
        # except likes from blocked users
        return api_blocked_users.get_likevotes_number(self=self, obj=obj)

    def get_comment_number(self, obj):
        # except comments from blocked users
        return api_blocked_users.get_comments_number(self=self, obj=obj)

    def get_drank_it_too_number(self, obj):
        # except drank_it_toos from blocked users
        return api_blocked_users.get_drank_it_toos_number(self=self, obj=obj)

    class Meta:
        model = Post
        fields = ['id', 'author', 'author_id', 'author_avatar_url',
                  'author_has_badge', 'author_badge_expiry_date_ms', 'expert',
                  'expert_id', 'expert_avatar_url', 'title', 'description',
                  'wine_year', 'post_id', 'post_main_image', 'wine_main_image',
                  'wine_ref_image', 'wine_ref_image_id', 'vuf_rating_tracking',
                  'vuf_rating_reco', 'vuf_match_post_status',
                  'vuf_match_post_title', 'vuf_match_post_id',
                  'vuf_match_post_pp', 'vuf_match_post_ref_image_id',
                  'vuf_match_rating_tracking', 'vuf_match_post_wm_natural',
                  'vuf_match_post_year', 'vuf_match_wine_name',
                  'vuf_match_wine_id', 'vuf_match_wine_status',
                  'vuf_match_wine_wm_natural', 'wm_natural', 'place_id',
                  'place_name', 'place_free_glass',
                  'place_free_glass_signup_date', 'place_gfg_count',
                  'place_i_got', 'foursquare_place_name',
                  'foursquare_place_url', 'is_star_review', 'is_parent_post',
                  'created_time', 'modified_time', 'likevote_number',
                  'comment_number', 'drank_it_too_number',
                  'star_review_number', 'wine_data', 'place_data',
                  'post_status', 'in_doubt', 'type', 'is_archived', 'mentions',
                  'wine_trade', 'free_so2', 'total_so2', 'is_scanned',
                  'is_organic', 'is_biodynamic', 'certified_by', 'tap_number',
                  'impression_number', 'price', 'currency',
                  'wine_main_image_id', 'wine_id', 'wine',
                  'vuf_match_post_ref_image', 'i_like_it', 'i_drank_it_too']


class FullPostSerializer(PostSerializer):
    # equivalent of to_dict_api
    # old default was include_wine_data=True

    def get_wine_data(self, obj):
        if (
            self.context.get('include_wine_data') and
            obj.type == PostTypeE.WINE
        ):
            return FullWineSerializer(obj.wine, context=self.context).data

        return None

    def to_representation(self, obj):
        data = super().to_representation(obj)

        get_free_so2_data = obj.get_free_so2()
        data['free_so2'] = get_free_so2_data['free_so2']
        data['total_so2'] = get_free_so2_data['total_so2']
        data['grape_variety'] = get_free_so2_data['grape_variety']

        api_status_legacy_data = api_status_winepost(obj)
        data['status'] = api_status_legacy_data['status']
        data['wine_kind'] = api_status_legacy_data['wine_kind']

        if 'in_doubt' in api_status_legacy_data:
            data['in_doubt'] = api_status_legacy_data['in_doubt']

        return data


class TimelinePostSerializer(PostSerializer):
    # equivalent of to_dict_api_tl
    # old default was include_wine_data=True
    def get_wine_data(self, obj):
        if (
            self.context.get('include_wine_data') and
            obj.type == PostTypeE.WINE
        ):
            return FullWineSerializer(obj.wine, context=self.context).data

        return None

    def to_representation(self, obj):
        data = super().to_representation(obj)

        get_free_so2_data = obj.get_free_so2()
        data['free_so2'] = get_free_so2_data['free_so2']
        data['total_so2'] = get_free_so2_data['total_so2']
        data['grape_variety'] = get_free_so2_data['grape_variety']

        api_status_legacy_data = api_status_winepost_tl(obj)
        data['status'] = api_status_legacy_data['status']
        data['post_status'] = api_status_legacy_data['post_status']
        data['post_kind'] = api_status_legacy_data['post_kind']

        if 'in_doubt' in api_status_legacy_data:
            data['in_doubt'] = api_status_legacy_data['in_doubt']

        return data


class PostUDSerializer(serializers.ModelSerializer):
    post_id = serializers.IntegerField(source="id")
    post_main_image = ImageUrlField(source='main_image')

    def to_representation(self, obj):
        data = super().to_representation(obj)

        api_status_legacy_data = api_status_winepost(obj)
        if obj.type == PostTypeE.WINE:
            data['status'] = api_status_legacy_data['status']
            data['wine_kind'] = api_status_legacy_data['wine_kind']
        else:
            data['status'] = obj.status
            data['wine_kind'] = None

        return data

    class Meta:
        model = Post
        fields = ['post_id', 'post_main_image']


class PostGetSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(required=True)


class VuforiaScansCountSerializer(serializers.Serializer):
    env = serializers.ChoiceField(required=False, choices=AppEnvE.pairs)


class SearchQuerySerialiser(serializers.Serializer):
    query = serializers.CharField(required=False)
    query_type = serializers.CharField(required=False)
    force_winepost_name_only = serializers.BooleanField(required=False)
    min_letters = serializers.IntegerField(required=False)
