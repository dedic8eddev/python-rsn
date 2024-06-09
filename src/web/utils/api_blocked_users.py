from reports.models import BlockUser


def get_blocked_users(self):
    return BlockUser.objects.filter(
        user=self.context['request'].user).values_list('block_user_id')


def get_likevotes_number(self, obj):
    # except likes from blocked users
    if self.context['request'].user.is_authenticated:
        blocked_users = get_blocked_users(self=self)
        return obj.like_votes.filter(is_archived=False).exclude(
            author_id__in=blocked_users
        ).count()
    else:
        return obj.like_votes.filter(is_archived=False).count()


def get_comments_number(self, obj):
    # except comments from blocked users
    if self.context['request'].user.is_authenticated:
        blocked_users = get_blocked_users(self=self)
        return obj.comments.filter(is_archived=False).exclude(
            author_id__in=blocked_users
        ).count()
    else:
        return obj.comments.filter(is_archived=False).count()


def get_drank_it_toos_number(self, obj):
    # except drank_it_toos from blocked users
    if self.context['request'].user.is_authenticated:
        blocked_users = get_blocked_users(self=self)
        return obj.drank_it_toos.filter(is_archived=False).exclude(
            author_id__in=blocked_users
        ).count()
    else:
        return obj.drank_it_toos.filter(is_archived=False).count()
