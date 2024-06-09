import datetime
import io
import json

import pyheif
from django.core.files.base import ContentFile
from django.http.request import RawPostDataException
from django.utils.translation import ugettext_lazy as _
from PIL import Image

from web.constants import PlaceImageAreaE
from web.models import Place, PlaceImage, PlaceOpeningHoursWeek
from web.utils.filenames import get_extension, replace_ext_with_jpg
from web.utils.upload_tools import aws_url
from web_pro.utils.common import get_owner_user, get_user_venue


class PlaceData:
    def __init__(self, request):
        self.data = self.get_data(request)
        self.user = get_owner_user(request)
        self.files = request.FILES
        self.place = get_user_venue(self.user.id, request)

    def get_place_opening_hours_week(self):
        return PlaceOpeningHoursWeek.active.filter(
            place=self.place
        ).first() if self.place else None

    @staticmethod
    def get_data(request):
        try:
            return json.loads(request.body)
        except (ValueError, RawPostDataException):
            return request.GET if request.GET else request.POST


class PlaceOperator(PlaceData):

    @staticmethod
    def parse_to_hour_minutes(opening_hours):
        open_from, open_to = opening_hours
        open_from_h, open_from_m = open_from.split(":")
        open_to_h, open_to_m = open_to.split(":")
        return {
            'fh': open_from_h,
            'fm': open_from_m,
            'th': open_to_h,
            'tm': open_to_m
        }

    def parse_opening_hours(self, hours_list):
        opening_hours1, opening_hours2 = hours_list
        opening_hours1_dict = self.parse_to_hour_minutes(opening_hours1)
        opening_hours2_dict = self.parse_to_hour_minutes(
            opening_hours2
        ) if opening_hours2 else {}

        return [opening_hours1_dict, opening_hours2_dict]

    @staticmethod
    def parse_holiday_date(date):
        date = date.replace(' ', '')
        dates = date.split('-')

        try:
            date_from = datetime.datetime.strptime(dates[0], '%d/%m/%Y')
        except ValueError:
            month, day, year = dates[0].split("/")
            holiday = f'{day}/{month}/{year}'
            date_from = datetime.datetime.strptime(holiday, '%d/%m/%Y')

        if len(dates) == 1:
            date_to = date_from + datetime.timedelta(days=1, microseconds=-1)
        elif len(dates) == 2:
            try:
                date_to = datetime.datetime.strptime(dates[1], '%d/%m/%Y')
            except ValueError:
                month, day, year = dates[1].split("/")
                holiday = f'{day}/{month}/{year}'
                date_to = datetime.datetime.strptime(holiday, '%d/%m/%Y')
            date_to = date_to + datetime.timedelta(days=1, microseconds=-1)

        return date_from.strftime(
            '%Y-%m-%dT%H:%M:%S%z'
        ), date_to.strftime('%Y-%m-%dT%H:%M:%S%z')

    def get_anchor(self):
        anchor = self.data.get('anchor', None)
        return '#' + anchor if anchor else ''

    def parse_holidays(self, holidays_list):
        parsed_holidays = []
        for holiday in holidays_list:
            date_from, date_to = self.parse_holiday_date(holiday)
            parsed_holidays.append({'f': date_from, 't': date_to, 'd': ''})
        return parsed_holidays

    def parse_date_range(self, date_range):
        parsed_date_range = []
        for dates in date_range:
            date_from, date_to = self.parse_holiday_date(dates)
            parsed_date_range.append({'f': date_from, 't': date_to, 'd': ''})
        return parsed_date_range

    def parse_data(self):
        """
        parse data at save
        :return: list
        """
        holidays = self.data.pop('holidays', [])
        date_range = self.data.pop('date_range', [])
        if holidays:
            holidays = self.parse_holidays(holidays)

        if date_range:
            date_range = self.parse_date_range(date_range)

        place_hours = {}
        for day, hours in self.data.items():
            if not hours:
                place_hours[day] = []
            else:
                place_hours[day] = self.parse_opening_hours(hours)

        return place_hours, holidays, date_range

    def handle_heic(self, file):
        i = pyheif.read_heif(file)
        jpg_img = Image.frombytes(mode=i.mode, size=i.size, data=i.data)
        output = io.BytesIO()
        jpg_img.save(output, format="jpeg")
        output.seek(0)
        filename = replace_ext_with_jpg(file.name)
        file = ContentFile(output.read())
        file.content_type = 'image/jpeg'
        file.name = filename

        return file

    def update_team_logo(self, file):
        self.remove_place_team_logo()
        file.name = "%s--%s" % (self.place.id, file.name)

        extension = get_extension(file.name).lower().strip('.')
        if extension == 'heic':
            self.handle_heic(file)

        team_logo = PlaceImage(
            image_file=file, place=self.place,
            author=self.user, image_area=PlaceImageAreaE.TEAM
        )
        team_logo.save()

    def update_place_logo(self, file):
        self.remove_place_logo()
        file.name = "%s--%s" % (self.place.id, file.name)

        extension = get_extension(file.name).lower().strip('.')
        if extension == 'heic':
            self.handle_heic(file)

        main_image = PlaceImage(
            image_file=file, place=self.place, author=self.user
        )
        main_image.save()
        self.place.main_image = main_image
        self.place.save()

    def update_place_images(self):
        if not self.place:
            return {}

        images = []

        for i, file in enumerate(list(self.files.items())):
            attr, image = file
            image.name = "%s--%s" % (self.place.id, image.name)
            area = getattr(PlaceImageAreaE, attr.split('[')[0])
            images.append(self.add_place_image(image, area))

        return {'image': [aws_url(image, thumb=True) for image in images]}

    def remove_place_logo(self, and_save=False):
        if self.place.main_image:
            self.place.main_image.archive()
            self.place.main_image = None
            if and_save:
                self.place.save()

    def remove_team_logo(self, and_save=False):
        team_image = PlaceImage.active.filter(
            place=self.place, image_area=PlaceImageAreaE.TEAM
        ).first()

        if team_image:
            team_image.archive()
            team_image.save()

    def remove_place_team_logo(self):
        team_image = PlaceImage.active.filter(
            author=self.user, place=self.place,
            image_area=PlaceImageAreaE.TEAM
        ).first()

        if team_image:
            team_image.image_area = PlaceImageAreaE.ARCHIVED
            team_image.archive()
            team_image.save()

    def add_place_image(self, file, area):
        next_ordering = self.place.place_images.filter(
            image_area=area, is_archived=False
        ).first()

        ordering_i = 0 if (
            not next_ordering or not next_ordering.ordering
        ) else next_ordering + 1

        area_image = PlaceImage(
            image_file=file,
            place=self.place,
            image_area=area,
            author=self.user,
            ordering=ordering_i
        )
        area_image.save()
        return area_image

    def update_place_hours(self):
        if not self.place:
            return {}

        hours, holidays, date_range = self.parse_data()

        self.place.opening_hours = hours
        self.place.closing_dates = holidays + date_range
        self.place.save(modified_time=False)
        return hours, holidays, date_range

    def update_place_info(self):
        if not self.place:
            return {}

        attributes = ('email', 'website_url', 'social_facebook_url',
                      'social_twitter_url', 'social_instagram_url',
                      'is_restaurant', 'is_bar', 'is_wine_shop', 'formitable_url')

        phone_number = self.data.get('phone_number', '')
        if phone_number:
            self.place.phone_number = phone_number
            self.place.save(modified_time=False)
        else:
            for attribute in attributes:
                value = self.data.get(attribute, False)
                if attribute == 'formitable_url' \
                        and hasattr(self.place, 'owner') \
                        and hasattr(self.place.owner, 'formitable_url'):
                    if not value:
                        value = ''
                    else:
                        str_add = '?ft-tag=Raisin'
                        value = (value.replace(str_add, '') + str_add)
                    setattr(self.place.owner, attribute, value)
                    self.place.owner.save()
                if value == 'on':
                    value = True
                setattr(self.place, attribute, value)

        self.place.save(modified_time=False)


class PlaceDataOperator(PlaceData):

    @staticmethod
    def parse_opening_hours(opening_hours):
        fh_str = str(opening_hours["fh"]).zfill(2)
        fm_str = str(opening_hours["fm"]).zfill(2)
        th_str = str(opening_hours["th"]).zfill(2)
        tm_str = str(opening_hours["tm"]).zfill(2)

        open_from = f'{fh_str}:{fm_str}'
        open_to = f'{th_str}:{tm_str}'

        return [open_from, open_to]

    @staticmethod
    def generate_hour_row(day, row, hours):
        html_id = ('#day{}-time{}-from', '#day{}-time{}-to')

        hour_from, hour_to = hours
        hour_from_id = html_id[0].format(day, row)
        hour_to_id = html_id[1].format(day, row)

        return [[hour_from_id, hour_from], [hour_to_id, hour_to]]

    @staticmethod
    def parse_holiday_date(date_dict):
        f_date = date_dict['f'].split('T')[0]
        f_year, f_month, f_day = f_date.split('-')

        t_date = date_dict['t'].split('T')[0]

        if f_date == t_date:
            return f'{f_day}/{f_month}/{f_year}'

    @staticmethod
    def parse_holiday_date_range(date_dict):
        f_date = date_dict['f'].split('T')[0]
        f_year, f_month, f_day = f_date.split('-')

        t_date = date_dict['t'].split('T')[0]
        t_year, t_month, t_day = t_date.split('-')

        if f_date != t_date:
            return f'{f_day}/{f_month}/{f_year} - {t_day}/{t_month}/{t_year}'

    def archive_old_images(self, images):
        if len(images) > 4:
            for image in images[4:]:
                image.image_area = PlaceImageAreaE.ARCHIVED
                image.archive()
            images = images[:3]
        return images

    def get_place_images(self):
        area = getattr(PlaceImageAreaE, self.data.get('area'))
        place_images = PlaceImage.active.filter(
            author=self.user, image_area=area
        ).order_by('modified_time')

        if not place_images:
            return {'result': []}

        return {
            'result': [aws_url(image, thumb=True) for image in place_images]
        }

    def get_team_image(self):
        return PlaceImage.active.filter(
            author=self.user, place=self.place,
            image_area=PlaceImageAreaE.TEAM
        ).first()

    def get_holidays(self):
        holidays_list = self.place.closing_dates if self.place else None

        if not holidays_list:
            return []
        return [self.parse_holiday_date(holiday) for holiday in holidays_list if self.parse_holiday_date(holiday)]

    def get_holidays_range(self):
        holidays_list = self.place.closing_dates if self.place else None

        if not holidays_list:
            return []
        return [self.parse_holiday_date_range(holiday) for holiday in holidays_list if
                self.parse_holiday_date_range(holiday)]

    def get_opening_hours(self, day):
        opening_hours = self.place.opening_hours if self.place else None
        if not self.place.opening_hours_defined():
            opening_hours = Place.get_default_opening_hours()

        if str(day) in opening_hours and opening_hours[str(day)]:
            day_to_use = str(day)
        elif int(day) in opening_hours and opening_hours[int(day)]:
            day_to_use = int(day)
        else:
            return []

        opening_hours1, opening_hours2 = opening_hours[day_to_use]
        opening_hours1_list = self.parse_opening_hours(opening_hours1)
        opening_hours2_list = self.parse_opening_hours(
            opening_hours2
        ) if opening_hours2 else []

        return [opening_hours1_list, opening_hours2_list]

    def get_place_types(self):
        attributes = ('is_bar', 'is_restaurant', 'is_wine_shop')
        place_types = {}
        for attribute in attributes:
            place_types[attribute] = getattr(self.place, attribute)

        return place_types

    def get_place_data(self):
        if not self.place:
            return {}
        attributes = ('name', 'email', 'website_url', 'social_facebook_url',
                      'social_twitter_url', 'social_instagram_url', 'city',
                      'country', 'state', 'zip_code', 'phone_number',
                      'formitable_url')
        place_data = {}
        for attribute in attributes:
            if attribute in ['city', 'country', 'zip_code', 'state']:
                val = getattr(self.place, attribute) if getattr(
                    self.place, attribute
                ) else 'n/a'
            elif attribute == 'formitable_url' \
                    and hasattr(self.place, 'owner') \
                    and hasattr(self.place.owner, attribute):
                val = getattr(self.place.owner, attribute)
                if val:
                    val = str(val).replace("?ft-tag=Raisin", "")
            else:
                val = getattr(self.place, attribute)
            place_data[attribute] = val

        full_street_address = getattr(self.place, 'full_street_address')
        street_address = getattr(self.place, 'street_address')
        if full_street_address:
            address = full_street_address
        elif street_address:
            address = street_address
        else:
            address = 'n/a'

        place_data['address'] = address

        place_description = getattr(self.place, 'description')
        if place_description == '' or place_description == '<p><br></p>':
            place_description = _(
                "🙋🏻 Please, complete this description to let users "
                "know what your venue is all about!"
            )

        place_data['description'] = place_description
        place_data['types'] = self.get_place_types()

        image_path = aws_url(
            self.place.main_image,
            thumb=True, fallback=False
        )

        team_image = self.get_team_image()
        team_image_path = aws_url(team_image, thumb=True, fallback=False)

        place_data['ref_image_id'] = image_path
        place_data['team_image'] = team_image_path
        place_data['latitude'] = self.place.latitude
        place_data['longitude'] = self.place.longitude
        place_data['pin_longitude'] = self.place.pin_longitude
        place_data['pin_latitude'] = self.place.pin_latitude

        return place_data

    def get_place_opening_hours_and_holidays(self):
        html_id = (
            '#opening-day{}', '#day{}-time{}-from',
            '#day{}-time{}-to', '#add-hours-{}'
        )

        opening_hours_and_holidays = {
            'holidays': self.get_holidays(),
            'date_range': self.get_holidays_range()
        }

        for day in range(1, 8):
            add_hours = False
            day_hours = self.get_opening_hours(str(day))
            active = True if day_hours else False
            opening_day_id = html_id[0].format(day)

            hours = []
            if active:
                hours1, hours2 = day_hours
                hours = self.generate_hour_row(day, 1, hours1)

                if hours2:
                    add_hours = html_id[3].format(day)
                    hours += self.generate_hour_row(day, 2, hours2)

            opening_hours_and_holidays[day] = {
                'active': [opening_day_id, active],
                'add_hours': add_hours,
                'hours': hours
            }

        return opening_hours_and_holidays
