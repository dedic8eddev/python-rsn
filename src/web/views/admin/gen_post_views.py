import datetime as dt
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_protect

from web.constants import PostStatusE, PostTypeE, SpecialStatusE
from web.forms.admin_forms import AdminFoodForm, AdminGeneralPostForm
from web.models import Comment, LikeVote, Post, PostImage

from web.serializers.comments_likes import CommentSerializer, LikeVoteSerializer
from web.utils.mentions import strip_description_update_user_mentions_indexes
from web.views.admin.common import get_c


# /posts
@login_required
def generalposts(request):
    c = get_c(
        request=request,
        active='list_generalposts',
        path='/posts',
        add_new_url='add_generalpost'
    )
    return render(request, "lists/generalposts.html", c)


@login_required
def food(request):
    c = get_c(
        request=request, active='list_food',
        path='/food', add_new_url='add_food'
    )
    return render(request, "lists/food.html", c)


# /post/add
@csrf_protect
@login_required
def add_generalpost(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_generalposts'), 'posts'),
        (reverse('add_generalpost'), 'add')
    ]

    c = get_c(
        request=request, active='list_posts',
        path=None, bc_path_alt=bc_path
    )

    post = Post(
        type=PostTypeE.NOT_WINE,
        author=c['current_user'],
        status=PostStatusE.DRAFT
    )

    if request.method == 'POST':
        form = AdminGeneralPostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            images = request.FILES.getlist('image')
            if post.status == PostStatusE.PUBLISHED:
                post.published_time = dt.datetime.now()

            post.save()
            post.refresh_from_db()

            if images:
                post_image = PostImage(image_file=images[0], post=post)
                post_image.save()
                post.main_image = post_image
                post.save()
                post.refresh_from_db()

            post.refresh_from_db()

            return redirect('edit_generalpost', post.id)

    else:
        form = AdminGeneralPostForm(instance=post)

    c["form"] = form
    c["post"] = post
    c["is_new"] = True
    c['current_status'] = PostStatusE.names[
        post.status
    ] if post.status in PostStatusE.names else None
    c["action_url"] = reverse('add_generalpost')

    c["pdg_title"] = "[New post]"

    opts_in = PostStatusE.names
    c["pdg_options"] = [
        {
            'value': PostStatusE.DRAFT,
            'name': opts_in[PostStatusE.DRAFT],
            'class': 'onhold', 'selclass': 'refused'
        },
        {
            'value': PostStatusE.PUBLISHED,
            'name': opts_in[PostStatusE.PUBLISHED],
            'class': 'btincluded',
            'selclass': 'included'
        },
    ]

    return render(request, "edit/generalpost.html", c)


# /post/edit/{id}
@login_required
@csrf_protect
def edit_generalpost(request, id):
    post = Post.objects.get(id=id)
    if post.type == PostTypeE.WINE:
        return redirect('edit_winepost', id)

    if post.type == PostTypeE.FOOD:
        return redirect('edit_food', id)

    if post.is_archived:
        post.status = SpecialStatusE.DELETE

    bc_path = [
        ('/', 'Home'),
        (reverse('list_generalposts'), 'posts'),
        (reverse('edit_generalpost', args=[id]), post.title),
    ]

    c = get_c(
        request=request, active='list_generalposts',
        path=None, bc_path_alt=bc_path
    )

    old_status = post.status

    if request.method == 'POST':
        form = AdminGeneralPostForm(request.POST, instance=post)
        if form.is_valid():
            cd = form.cleaned_data

            if cd['status'] == SpecialStatusE.DELETE:
                post.status = PostStatusE.DELETED
                post.save()
                post.refresh_from_db()
                post.archive()
                return redirect('list_generalposts')
            else:

                cd['user_mentions'] = post.user_mentions
                cd = strip_description_update_user_mentions_indexes(
                    cd, mentions_field='user_mentions'
                )

                images = request.FILES.getlist('image')

                post.last_modifier = c['current_user']
                last_modified_time = dt.datetime.now()
                post.modified_time = last_modified_time
                if (
                    post.status == PostStatusE.PUBLISHED and
                    old_status != PostStatusE.PUBLISHED
                ):
                    post.published_time = dt.datetime.now()
                post.is_archived = False
                post.save()
                post.refresh_from_db()

                if images:
                    post_image = PostImage(image_file=images[0], post=post)
                    post_image.save()
                    post.main_image = post_image
                    post.save()
                    post.refresh_from_db()

                post.refresh_from_db()

                if post.type == PostTypeE.FOOD:
                    return redirect('edit_food', id)

    else:
        form = AdminGeneralPostForm(instance=post)

    c["form"] = form
    c["post"] = post
    c["is_new"] = False

    c['current_status'] = None
    c["action_url"] = reverse('edit_generalpost', args=[id])
    c["comments"] = CommentSerializer(
        Comment.active.filter(post=post), many=True
    ).data
    c["likevotes"] = LikeVoteSerializer(
        LikeVote.active.filter(post=post), many=True
    ).data

    if post.last_modifier:
        c["saved_by"] = post.last_modifier
        c["saved_at"] = post.modified_time
    else:
        c["saved_by"] = post.author
        c["saved_at"] = post.created_time

    c["pdg_title"] = post.title

    c["pdg_option_classes"] = {
        PostStatusE.DRAFT: "onhold",
        PostStatusE.PUBLISHED: "btincluded",
    }

    opts_in = PostStatusE.names
    c["pdg_options"] = [
        {
            'value': PostStatusE.DRAFT,
            'name': opts_in[PostStatusE.DRAFT],
            'class': 'onhold',
            'selclass': 'onhold'
        },
        {
            'value': PostStatusE.PUBLISHED,
            'name': opts_in[PostStatusE.PUBLISHED],
            'class': 'btincluded',
            'selclass': 'included'
        },
        {
            'value': SpecialStatusE.DELETE,
            'name': _("Delete"), 'class': 'btrefused',
            'selclass': 'refused'
        }
    ]

    return render(request, "edit/generalpost.html", c)


@csrf_protect
@login_required
def add_food(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_food'), 'posts'),
        (reverse('add_food'), 'add')
    ]

    c = get_c(
        request=request, active='list_food', path=None, bc_path_alt=bc_path
    )

    post = Post(
        type=PostTypeE.FOOD,
        author=c['current_user'],
        status=PostStatusE.DRAFT
    )

    if request.method == 'POST':
        form = AdminFoodForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            images = request.FILES.getlist('image')
            if post.status == PostStatusE.PUBLISHED:
                post.published_time = dt.datetime.now()

            post.save()
            post.refresh_from_db()

            if images:
                post_image = PostImage(image_file=images[0], post=post)
                post_image.save()
                post.main_image = post_image
                post.save()
                post.refresh_from_db()

            post.refresh_from_db()

            return redirect('edit_food', post.id)

    else:
        form = AdminFoodForm(instance=post)

    c["form"] = form
    c["post"] = post
    c["is_new"] = True
    c['current_status'] = PostStatusE.names[
        post.status
    ] if post.status in PostStatusE.names else None
    c["action_url"] = reverse('add_food')

    c["pdg_title"] = "[New post]"

    opts_in = PostStatusE.names
    c["pdg_options"] = [
        {
            'value': PostStatusE.DRAFT,
            'name': opts_in[PostStatusE.DRAFT],
            'class': 'onhold',
            'selclass': 'refused'
        },
        {
            'value': PostStatusE.PUBLISHED,
            'name': opts_in[PostStatusE.PUBLISHED],
            'class': 'btincluded',
            'selclass': 'included'
        },
    ]

    return render(request, "edit/food.html", c)


# /post/edit/{id}
@login_required
@csrf_protect
def edit_food(request, id):
    post = Post.objects.get(id=id)
    if post.type == PostTypeE.WINE:
        return redirect('edit_winepost', id)

    if post.type == PostTypeE.NOT_WINE:
        return redirect('edit_generalpost', id)

    if post.is_archived:
        post.status = SpecialStatusE.DELETE

    old_status = post.status

    bc_path = [
        ('/', 'Home'),
        (reverse('list_food'), 'posts'),
        (reverse('edit_food', args=[id]), post.title),
    ]

    c = get_c(
        request=request, active='list_food', path=None, bc_path_alt=bc_path
    )

    if request.method == 'POST':
        form = AdminFoodForm(request.POST, instance=post)
        if form.is_valid():
            cd = form.cleaned_data

            if cd['status'] == SpecialStatusE.DELETE:
                post.status = PostStatusE.DELETED
                post.save()
                post.refresh_from_db()
                post.archive()
                return redirect('list_food')
            else:

                cd['user_mentions'] = post.user_mentions
                cd = strip_description_update_user_mentions_indexes(
                    cd, mentions_field='user_mentions'
                )

                images = request.FILES.getlist('image')

                post.last_modifier = c['current_user']
                last_modified_time = dt.datetime.now()
                post.modified_time = last_modified_time
                post.is_archived = False
                if (
                    post.status == PostStatusE.PUBLISHED and
                    old_status != PostStatusE.PUBLISHED
                ):
                    post.published_time = dt.datetime.now()

                post.save()
                post.refresh_from_db()

                if images:
                    post_image = PostImage(image_file=images[0], post=post)
                    post_image.save()
                    post.main_image = post_image
                    post.save()
                    post.refresh_from_db()

                post.refresh_from_db()

    else:
        form = AdminFoodForm(instance=post)

    c["form"] = form
    c["post"] = post
    c["is_new"] = False
    c['current_status'] = None
    c["action_url"] = reverse('edit_food', args=[id])
    c["comments"] = CommentSerializer(
        Comment.active.filter(post=post), many=True
    ).data
    c["likevotes"] = LikeVoteSerializer(
        LikeVote.active.filter(post=post), many=True
    ).data

    if post.last_modifier:
        c["saved_by"] = post.last_modifier
        c["saved_at"] = post.modified_time
    else:
        c["saved_by"] = post.author
        c["saved_at"] = post.created_time

    c["pdg_title"] = post.title

    c["pdg_options"] = PostStatusE.pairs
    c["pdg_option_classes"] = {
        PostStatusE.DRAFT: "onhold",
        PostStatusE.PUBLISHED: "btincluded",
    }

    opts_in = PostStatusE.names
    c["pdg_options"] = [
        {
            'value': PostStatusE.DRAFT,
            'name': opts_in[PostStatusE.DRAFT],
            'class': 'onhold',
            'selclass': 'onhold'},
        {
            'value': PostStatusE.PUBLISHED,
            'name': opts_in[PostStatusE.PUBLISHED],
            'class': 'btincluded',
            'selclass': 'included'
        },
        {
            'value': SpecialStatusE.DELETE,
            'name': _("Delete"), 'class': 'btrefused',
            'selclass': 'refused'
        }
    ]

    return render(request, "edit/food.html", c)
