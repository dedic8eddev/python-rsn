from datetime import datetime

import factory

from web.constants import (PlaceTypeE, PostStatusE, PostTypeE, StatusE,
                           TimeLineItemTypeE, UserTypeE, WineColorE,
                           WinemakerStatusE)
from web.models import (Place, Post, TimeLineItem, UserProfile, Wine, Winemaker,
                        generate_key)


class UserProfileFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = UserProfile

    username = factory.Sequence(lambda x: 'testuser{}'.format(x))
    email = factory.sequence(lambda x: 'testuser{}@raisintest.eu'.format(x))

    id = factory.Faker('uuid4')
    key = generate_key()

    # push_fields are for push notifications
    push_user_id = None
    push_user_token = None

    created_time = datetime.now()
    modified_time = datetime.now()

    full_name = factory.Sequence(lambda x: 'Test Customer {}'.format(x))
    description = 'Test description'

    type = UserTypeE.ADMINISTRATOR
    status = StatusE.DRAFT

    is_archived = False
    is_confirmed = True
    is_owner = True


class WineMakerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Winemaker

    author = factory.SubFactory(UserProfileFactory, type=UserTypeE.USER)
    created_time = datetime.now()
    modified_time = datetime.now()

    status = WinemakerStatusE.VALIDATED

    # main data fields:
    name = factory.Sequence(lambda x: 'winemaker{}'.format(x))
    name_short = factory.Sequence(lambda x: 'short_winemaker{}'.format(x))
    description = factory.Sequence(lambda x: 'description{}'.format(x))

    domain = factory.Sequence(lambda x: 'domain{}'.format(x))
    domain_short = factory.Sequence(lambda x: 'short_domain{}'.format(x))
    domain_description = factory.Sequence(
        lambda x: 'description_domain{}'.format(x)
    )

    street_address = factory.Sequence(lambda x: 'street{}'.format(x))
    full_street_address = factory.Sequence(lambda x: 'full_street{}'.format(x))

    in_doubt = False
    is_archived = False
    is_organic = False
    is_biodynamic = False

    # social sites
    social_facebook_url = ""
    social_twitter_url = ""
    social_instagram_url = ""


class WineFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Wine

    created_time = datetime.now()
    modified_time = datetime.now()

    status = StatusE.PUBLISHED
    is_archived = False

    validated_at = datetime.now()
    validated_by = None

    # main data fields
    name = factory.Sequence(lambda x: 'wine{}'.format(x))
    name_short = factory.Sequence(lambda x: 'short{}'.format(x))
    domain = factory.Sequence(lambda x: 'domain{}'.format(x))
    designation = factory.Sequence(lambda x: 'designation{}'.format(x))
    grape_variety = factory.Sequence(lambda x: 'grape_variety{}'.format(x))
    region = factory.Sequence(lambda x: 'region{}'.format(x))

    color = WineColorE.RED
    year = '1997'
    is_sparkling = False

    similiar_wine_exists = False

    author = factory.SubFactory(UserProfileFactory, type=UserTypeE.USER)
    winemaker = factory.SubFactory(WineMakerFactory)


class PlaceFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Place

    created_time = datetime.now()
    modified_time = datetime.now()
    status = StatusE.PUBLISHED
    name = factory.Sequence(lambda x: 'place{}'.format(x))
    type = PlaceTypeE.WINE_SHOP
    description = factory.Sequence(lambda x: 'description{}'.format(x))
    author = factory.SubFactory(UserProfileFactory)


class WinePostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    parent_post = None
    last_modifier = None
    expert = None
    author = factory.SubFactory(UserProfileFactory, type=UserTypeE.USER)
    wine = factory.SubFactory(WineFactory)
    place = factory.SubFactory(PlaceFactory, type=30)

    created_time = datetime.now()
    modified_time = datetime.now()

    # main data fields
    title = factory.Sequence(lambda x: 'title{}'.format(x))
    description = factory.Sequence(lambda x: 'description{}'.format(x))
    status = PostStatusE.PUBLISHED
    type = PostTypeE.WINE


class FoodPostFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Post

    parent_post = None
    last_modifier = None
    expert = None
    author = factory.SubFactory(UserProfileFactory)
    place = factory.SubFactory(PlaceFactory, type=30)

    created_time = datetime.now()
    modified_time = datetime.now()

    # main data fields
    title = factory.Sequence(lambda x: 'title{}'.format(x))
    description = factory.Sequence(lambda x: 'description{}'.format(x))
    status = PostStatusE.PUBLISHED
    type = PostTypeE.FOOD


class TimeLineItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = TimeLineItem

    author = factory.SubFactory(UserProfileFactory, type=UserTypeE.USER)
    created_time = datetime.now()
    modified_time = datetime.now()

    post_item = factory.SubFactory(WinePostFactory)
    item_description = "abcd"
    item_type = TimeLineItemTypeE.POST
