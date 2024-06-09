import re

import web.models

from .model_tools import load_json
from .sendernotifier import SenderNotifier


def format_mentions(user_mentions):
    mentions_out = []
    if isinstance(user_mentions, list):
        mentions_out = user_mentions
    elif isinstance(user_mentions, dict):
        mentions_out = user_mentions
    elif isinstance(user_mentions, str):
        mentions_out = load_mentions_json_or_empty(user_mentions)

    if not mentions_out or mentions_out is None:
        mentions_out = []
    return mentions_out


def load_mentions_json_or_empty(mentions_text):
    if mentions_text and mentions_text != '{}' and mentions_text != '[]':
        mentions_json = load_json(mentions_text, [])
        return mentions_json
    else:
        return []


# left strip update =======================================
def strip_description_update_user_mentions_indexes(
    cd, desc_field='description', mentions_field='mentions'
):
    mentions_out = []
    description = cd[desc_field] if desc_field in cd else ''
    if description:
        desc_strip = description
    else:
        cd[mentions_field] = []
        return cd

    # search for all mentions in the text
    # re.search(r'\s@[0-9A-Za-z_]+|\A@[0-9A-Za-z_]+',
    if cd[mentions_field]:
        for i, mention in enumerate(cd[mentions_field]):
            username = mention['user_name']
            if username[0] == '@':
                mnt_s = username
            else:
                mnt_s = '@' + username

            mnt_x_0 = re.search(r'\s(%s)' % mnt_s, desc_strip)
            mnt_x_1 = re.search(r'\A(%s)' % mnt_s, desc_strip)
            if not mnt_x_0 and not mnt_x_1:
                start = None
                continue
            elif mnt_x_0:
                start = mnt_x_0.span(1)[0]
            elif mnt_x_1:
                start = mnt_x_1.span(1)[0]

            mention['start_index'] = start
            mentions_out.append(mention)

    cd[mentions_field] = mentions_out
    cd[desc_field] = desc_strip
    return cd


def update_user_mentions_fn(
    self, mentions_out, mentions_field='user_mentions', save_item=False
):
    mentions_old = getattr(self, mentions_field)
    usernames_old = [mention['user_name'] for mention in mentions_old] if mentions_old else []  # noqa
    usernames_out = [mention['user_name'] for mention in mentions_out] if mentions_out else []  # noqa
    start_index_by_username = {}
    new_usernames = []
    if not mentions_out:
        mentions_out = []

    for mnt in mentions_out:
        username = mnt['user_name']
        start_index = mnt['start_index']
        start_index_by_username[username] = start_index

    new_usernames = [
        name for name in usernames_out if name not in usernames_old
    ]

    setattr(self, mentions_field, mentions_out)
    if isinstance(self, web.models.Comment):
        send_mentioned_method = SenderNotifier().send_mentioned_comment
    elif isinstance(self, web.models.Post):
        send_mentioned_method = SenderNotifier().send_mentioned_post
    elif isinstance(self, web.models.Place):
        send_mentioned_method = SenderNotifier().send_mentioned_place
    else:
        return

    if new_usernames:
        for username in new_usernames:
            user_objs = web.models.UserProfile.active.filter(
                username=username.replace('@', '')
            )
            if user_objs:
                user_obj = user_objs[0]
                # adding mention for new username %s
                if username in start_index_by_username:
                    start_index = start_index_by_username[username]
                    send_mentioned_method(user_obj, self, start_index)
            else:  # username %s not found
                continue

    if save_item:
        self.save()
