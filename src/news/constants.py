from web.utils.enum import EnumMetaclass


class NewsStatus(metaclass=EnumMetaclass):
    DRAFT = 10
    PUBLISHED = 20
    DELETED = 30


WEBSITE_PAGES = {
    "our_mission": {"name": "Our Mission", "url": "our-mission"},
    "ambassadors": {"name": "Ambassadors", "url": "ambassadors"},
    "team": {"name": "Team", "url": "team"},
    "general_conditions": {"name": "General Conditions for Use", "url": "terms-and-conditions"},
    "privacy_policy": {"name": "Privacy Policy", "url": "privacy-policy"},
    "what_is_natural_wine": {"name": "What's Natural Wine?", "url": "what-is-natural-wine"},
    "all_venues_world": {"name": "5,000 venues all over the world.", "url": "world-all-venues"},
    "cities": {"name": "Cities", "url": "cities"},
    "countries": {"name": "Countries", "url": "countries"}
}
