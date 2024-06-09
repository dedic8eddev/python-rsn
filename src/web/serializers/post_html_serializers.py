from rest_framework import serializers

from web.constants import WineColorE
from web.models import Post
from web.utils.model_tools import cut_string
from web.views.ajax_lists.formatting import (format_geoloc_html,
                                             format_img_html_wp,
                                             format_user_html,
                                             format_vuforia_image,
                                             format_wine_label,
                                             format_winemaker_name,
                                             format_winepost_status,
                                             move_to_vuforia_arrow,
                                             winepost_title_html)


class BaseHTMLSerializer(serializers.ModelSerializer):
    checkbox_id = serializers.SerializerMethodField()
    img_html = serializers.SerializerMethodField()
    label_html = serializers.SerializerMethodField()
    winemaker_name = serializers.SerializerMethodField()

    domain = serializers.CharField(source="wine_winemaker_domain")
    designation = serializers.CharField(source="wine_designation")
    grape_variety = serializers.CharField(source="wine_grape_variety")
    year = serializers.CharField(source="wine_year")

    color_text = serializers.SerializerMethodField()
    sparkling_html = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()

    author_img_html = serializers.SerializerMethodField()
    price = serializers.SerializerMethodField()
    geolocation = serializers.SerializerMethodField()

    def get_checkbox_id(self, obj):
        cb = '<input id="colors-{}-toggle-1" name="ids" value="{}" type="checkbox">'  # noqa
        return cb.format(obj.id, obj.id)

    def get_img_html(self, obj):
        return format_img_html_wp(obj)

    def get_label_html(self, obj):
        return format_wine_label(obj)

    def get_winemaker_name(self, obj):
        return format_winemaker_name(obj)

    def get_author_img_html(self, obj):
        return format_user_html(obj.author)

    def get_expert_img_html(self, obj):
        return format_user_html(obj.expert)

    def get_color_text(self, obj):
        if obj.wine.color in WineColorE.names:
            color_name = WineColorE.names[obj.wine.color].capitalize()
            color_img = WineColorE.names[obj.wine.color].lower() + '.gif'

            ct = '<img data-original-title="{}" src="/static/assets/img/{}" ' \
                 'alt="{}" data-toggle="tooltip" title="" ' \
                 'data-placement="bottom" height="18" width="18">'
            return ct.format(color_name, color_img, color_name)
        else:
            return ''

    def get_sparkling_html(self, obj):
        if obj.wine.is_sparkling:
            return '<i class="fa fa-check-square" data-toggle="tooltip" ' \
                   'title="sparkling" data-placement="bottom"></i>'
        else:
            return '<i class="fa fa-square-o" data-toggle="tooltip" ' \
                   'title="not sparkling" data-placement="bottom"></i>'

    def get_description(self, obj):
        return "{} [{}]".format(
            cut_string(obj.description, 41),
            len(obj.description)
        ) if obj.description else ''

    def get_date(self, obj):
        return obj.modified_time.strftime('%d %b %Y %H:%M')

    def get_geolocation(self, obj):
        return format_geoloc_html(obj.place)

    def get_price(self, obj):
        if obj.price and obj.currency:
            price_part = obj.price
            currency = obj.currency if obj.currency else 'EUR'
            return "{} {}".format(price_part, currency)
        else:
            return ''

    def get_status_html(self, obj):
        return format_winepost_status(obj)

    def get_matched_html(self, obj):
        return format_vuforia_image(obj, with_rating=True)

    class Meta:
        model = Post
        fields = ['checkbox_id', 'img_html', 'label_html',
                  'winemaker_name', 'domain', 'designation',
                  'grape_variety', 'year', 'color_text',
                  'sparkling_html', 'date', 'author_img_html',
                  'geolocation', 'comment_number', 'price']


class WinepostWithVuforiaSerializer(BaseHTMLSerializer):
    status_html = serializers.SerializerMethodField()
    matched_html = serializers.SerializerMethodField()
    description = serializers.SerializerMethodField()
    # expert_img_html = serializers.SerializerMethodField()
    region = serializers.CharField(source="wine_winemaker_region")
    expert_img_html = serializers.SerializerMethodField()

    def get_img_html(self, obj):
        return format_img_html_wp(obj) + '<br/>' + winepost_title_html(obj)

    class Meta:
        model = Post
        fields = BaseHTMLSerializer.Meta.fields + [
            'status_html', 'matched_html', 'region', 'description',
            'expert_img_html'
        ]


class WinepostForWinemakerSerializer(BaseHTMLSerializer):
    status = serializers.SerializerMethodField()
    vuforia_img_html = serializers.SerializerMethodField()
    label_img_html = serializers.SerializerMethodField()
    title = serializers.SerializerMethodField()

    def get_status(self, obj):
        return format_winepost_status(obj)

    def get_img_html(self, obj):
        return format_wine_label(obj)

    def get_label_img_html(self, obj):
        return format_img_html_wp(obj)

    def get_vuforia_img_html(self, obj):
        return format_vuforia_image(obj)

    def get_title(self, obj):
        return winepost_title_html(obj)

    class Meta:
        model = Post
        fields = BaseHTMLSerializer.Meta.fields + [
            'status', 'vuforia_img_html', 'likevote_number',
            'drank_it_too_number', 'label_img_html', 'title'
        ]


class WinepostForWinepostSerializer(BaseHTMLSerializer):
    title = serializers.SerializerMethodField()
    vuforia_img_html = serializers.SerializerMethodField()
    posted_img_html = serializers.SerializerMethodField()
    status_html = serializers.SerializerMethodField()
    region = serializers.CharField(source="wine_winemaker_region")
    place_html = serializers.SerializerMethodField()

    def get_status(self, obj):
        return format_winepost_status(obj)

    def get_title(self, obj):
        return winepost_title_html(obj)

    def get_posted_img_html(self, obj):
        return format_img_html_wp(obj) + move_to_vuforia_arrow(
            obj, 'secondary'
        )

    def get_vuforia_img_html(self, obj):
        return format_vuforia_image(obj)

    def get_place_html(self, obj):
        return format_geoloc_html(obj.place)

    def get_author_img_html(self, obj):
        return format_user_html(obj.author, show_author_username=True)

    class Meta:
        model = Post
        fields = BaseHTMLSerializer.Meta.fields + [
            'status_html', 'likevote_number', 'drank_it_too_number', 'title',
            'description', 'vuforia_img_html', 'posted_img_html', 'region',
            'place_html'
        ]


class WinepostForRefereeSerializer(BaseHTMLSerializer):
    title = serializers.SerializerMethodField()
    status_html = serializers.SerializerMethodField()
    place_html = serializers.SerializerMethodField()
    region = serializers.CharField(source="wine_winemaker_region")
    winemaker = serializers.CharField(source="wine_winemaker_name")

    def get_place_html(self, obj):
        return format_geoloc_html(obj.place)

    def get_status(self, obj):
        return format_winepost_status(obj)

    def get_author_img_html(self, obj):
        return format_user_html(obj.author, show_author_username=True)

    def get_img_html(self, obj):
        return format_img_html_wp(obj)

    def get_title(self, obj):
        return winepost_title_html(obj)

    class Meta:
        model = Post
        fields = BaseHTMLSerializer.Meta.fields + [
            'title', 'description', 'status_html', 'region', 'place_html',
            'likevote_number', 'drank_it_too_number', 'winemaker'
        ]
