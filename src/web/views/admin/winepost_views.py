import datetime as dt
import logging
import re

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.csrf import csrf_protect

from web.constants import (PostStatusE, PostTypeE, SpecialStatusE, UserTypeE,
                           WinemakerStatusE)
from web.forms.admin_forms import AdminWinePostForm
from web.models import Place, Post, PostImage, TotalStats, WineImage, Winemaker
from web.helpers.winemakers import WinemakerHelper
from web.helpers.wineposts import WinepostHelper
from web.utils.mentions import strip_description_update_user_mentions_indexes
from web.utils.model_tools import make_winepost_title
from web.utils.upload_tools import get_url_with_random_suffix
from web.utils.vuforia_models import (create_vuforia_image_from_file,
                                      create_vuforia_images_for_post_and_wine)
from web.utils.yearly_data import empty_fields_in_yearly_data
from web.views.admin.common import get_c, get_wineposts_number

log = logging.getLogger(__name__)


@login_required
def wineposts(request):
    c = get_c(
        request=request, active='list_wineposts',
        path='/wineposts', add_new_url=None
    )
    c['add_wm_url'] = 'add_winemaker'
    c['opti'] = True
    stats_items = TotalStats.objects.all()
    if stats_items:
        c['vuforia_scans_total'] = stats_items[0].vuforia_scans_total
    else:
        c['vuforia_scans_total'] = 0

    owners_filter = Q(author__type__in=[
        UserTypeE.OWNER,
    ])
    geoloc_filter = Q(
        place__isnull=False,
        author__type=UserTypeE.USER
    )
    users_filter = Q(author__type=UserTypeE.USER)

    c['all_total'], c['all_drafts'] = get_wineposts_number(Q())
    c['owners_total'], c['owners_drafts'] = get_wineposts_number(owners_filter)
    c['geoloc_total'], c['geoloc_drafts'] = get_wineposts_number(geoloc_filter)
    c['users_total'], c['users_drafts'] = get_wineposts_number(users_filter)

    return render(request, "lists/wine-posts-pro.html", c)


# /all-star-reviews
@login_required
def all_star_reviews(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('list_star_reviews_all'), 'All star reviews')
    ]
    c = get_c(
        request=request, active='list_star_reviews_all',
        path=None, bc_path_alt=bc_path
    )
    c['add_wm_url'] = 'add_winemaker'
    return render(request, "lists/all-star-reviews.html", c)


# /all-referee-posts
@login_required
def all_referees(request):
    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('list_star_reviews_all'), 'All star reviews')
    ]
    c = get_c(
        request=request, active='list_wineposts',
        path=None, bc_path_alt=bc_path
    )
    c['add_wm_url'] = 'add_winemaker'
    return render(request, "lists/all-referees.html", c)


# /winepost/star-reviews/{id}
@login_required
def winepost_star_reviews(request, id):
    winepost = Post.active.get(id=id, type=PostTypeE.WINE)
    wine = winepost.wine

    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('edit_winepost', args=[id]), wine.name),
        (
            reverse('list_winepost_star_reviews', args=[id]),
            'Star reviews for ' + wine.name
        )
    ]

    c = get_c(
        request=request, active='list_wineposts', path=None,
        bc_path_alt=bc_path, add_new_url=None
    )

    # c['add_wm_url'] = 'add_winemaker_natural' if wine.winemaker.get_is_natural() else 'add_winemaker_other'  # noqa
    c['add_wm_url'] = 'add_winemaker'

    return render(request, "lists/wine-posts-star-reviews.html", c)


# /winepost/referees/{id}
@login_required
def winepost_referees(request, id):
    winepost = Post.active.get(id=id, type=PostTypeE.WINE)
    wine = winepost.wine

    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('edit_winepost', args=[id]), wine.name),
        (
            reverse('list_winepost_referees', args=[id]),
            'Referees for ' + wine.name
        )
    ]

    c = get_c(
        request=request, active='list_wineposts', path=None,
        bc_path_alt=bc_path, add_new_url=None
    )

    c['wine'] = wine
    c['winepost'] = winepost
    # c['add_wm_url'] = 'add_winemaker_natural' if wine.winemaker.get_is_natural() else 'add_winemaker_other'  # noqa
    c['add_wm_url'] = 'add_winemaker'

    return render(request, "lists/wine-posts-referees.html", c)


# /winemaker/star-reviews/{id}
@login_required
def winemaker_star_reviews(request, id):
    winemaker = Winemaker.active.get(id=id)

    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('edit_winemaker', args=[id]), winemaker.name),
        (
            reverse('winemaker_star_reviews', args=[id]),
            "Star reviews for wines by '%s'" % winemaker.name
        )
    ]

    c = get_c(
        request=request, active='list_wineposts', path=None,
        bc_path_alt=bc_path, add_new_url=None
    )

    c['winemaker'] = winemaker
    # c['add_wm_url'] = 'add_winemaker_natural' if winemaker.get_is_natural() else 'add_winemaker_other'  # noqa
    c['add_wm_url'] = 'add_winemaker'

    return render(request, "lists/winemaker-star-reviews.html", c)


# /winemaker/referee-posts/{id}
@login_required
def winemaker_referees(request, id):
    winemaker = Winemaker.active.get(id=id)

    bc_path = [
        ('/', 'Home'),
        (reverse('list_wineposts'), 'wineposts'),
        (reverse('edit_winemaker', args=[id]), winemaker.name),
        (
            reverse('winemaker_referees', args=[id]),
            "Referees for wines by '%s' " % winemaker.name
        )
    ]

    c = get_c(
        request=request, active='list_wineposts', path=None,
        bc_path_alt=bc_path, add_new_url=None
    )

    c['winemaker'] = winemaker
    # c['add_wm_url'] = 'add_winemaker_natural' if winemaker.get_is_natural() else 'add_winemaker_other'  # noqa
    c['add_wm_url'] = 'add_winemaker'

    return render(request, "lists/winemaker-posts-referees.html", c)


# /winepost/edit/{id}
@login_required
@csrf_protect
def edit_winepost(request, id):
    post = Post.objects.select_related('wine', 'place', 'wine__winemaker', 'author').get(id=id)
    if post.type == PostTypeE.NOT_WINE:
        return redirect('edit_generalpost', id)

    create_vuforia_images_for_post_and_wine(post)
    # if post.status == PostStatusE.HIDDEN:
    #     return redirect('list_wineposts')

    is_natural_winemaker = post.wine.winemaker.get_is_natural()
    is_natural_post = post.get_is_natural()

    # prepare related endpoints url names
    # active_url_name = WinepostHelper.get_active_endpoint_url_name(post, is_natural=is_natural_winemaker)
    add_wm_url = WinepostHelper.get_add_winemaker_endpoint_url_name(is_natural=is_natural_winemaker)
    # bc_path = WinepostHelper.get_bc_path(post, active_url_name)

    # get context
    # context = get_c(request=request, active=active_url_name, path=None, bc_path_alt=bc_path)
    context = {}

    is_original_winemaker_editable = False

    if post.wine.winemaker.status in [WinemakerStatusE.DRAFT, WinemakerStatusE.IN_DOUBT]:
        is_original_winemaker_editable = True

    context["original_winemaker_editable"] = is_original_winemaker_editable
    context['is_published'] = post.status == PostStatusE.PUBLISHED
    context['is_draft'] = True if post.status == PostStatusE.DRAFT else False
    context['current_user'] = request.user

    data_in = {
        'name': post.wine.name,
        'name_short': post.wine.name_short,
        'domain': WinepostHelper.get_winepost_domain(post),
        'designation': post.wine.designation,
        'grape_variety': post.grape_variety,
        'color': post.wine.color,
        'is_sparkling': post.wine.is_sparkling,
        'is_star_review': post.is_star_review,
        'team_comments': post.team_comments,

        'year': post.wine_year,
        'winemaker': post.wine.winemaker_id,
        # 'region': post.wine.region,
        'description': post.description,
        'geolocation': post.place.name if post.place else None,
        'place_id': post.place.id if post.place else None,
        'status': SpecialStatusE.DELETE if post.is_archived else post.status,
        'original_winemaker_name': WinemakerHelper.get_original_name(winemaker=post.wine.winemaker),
        'wine_trade': post.wine_trade,
        'free_so2': post.free_so2,
        'total_so2': post.total_so2,
        'is_parent_post': post.is_parent_post if post.status != PostStatusE.DRAFT else False,
        'is_biodynamic': post.is_biodynamic,
        'is_organic': post.is_organic,
        'certified_by': post.certified_by,
    }

    if request.method == 'POST':
        form = AdminWinePostForm(request.POST)
        if form.is_valid():
            images = request.FILES.getlist('image')
            wine_images = request.FILES.getlist('wine_image')
            ref_images = request.FILES.getlist('ref_image')
            cd = form.cleaned_data
            cd['user_mentions'] = post.user_mentions
            cd = strip_description_update_user_mentions_indexes(
                cd, mentions_field='user_mentions'
            )

            if cd['status'] == SpecialStatusE.DELETE:
                if not post.is_archived:
                    post.archive(modifier_user=request.user)
                    post.refresh_from_db()
            elif cd['status'] == SpecialStatusE.DUPLICATE:
                new_post = post.duplicate()
                return redirect("edit_winepost", **{'id': new_post.id})
            elif cd['status'] == SpecialStatusE.NOT_WINE:
                post = post.move_to_general_post()
                return redirect("edit_generalpost", **{'id': post.id})
            else:
                post_from_db = Post.objects.get(id=id)
                if post_from_db.is_archived:
                    post.unarchive()

            post.last_modifier = context['current_user']
            post.expert = context['current_user']
            last_modified_time = dt.datetime.now()
            post.modified_time = last_modified_time

            post.wine.name = cd['name']
            post.wine.name_short = cd['name_short']
            post.wine.domain = re.sub(r'\[DRAFT\]', "", cd['domain'])
            post.wine.designation = cd['designation']

            if cd['is_parent_post']:
                post.wine.grape_variety = cd['grape_variety']
                post.grape_variety = cd['grape_variety']
            else:
                post.grape_variety = cd['grape_variety']

            post.wine.color = cd['color']
            post.wine.is_sparkling = cd['is_sparkling']
            post.wine_year = cd['year']
            post.team_comments = cd['team_comments']

            post.description = cd['description']
            # post.title = cd['name']
            post.title = make_winepost_title(cd['name'], cd['year'])

            post.wine_trade = cd['wine_trade']
            post.free_so2 = cd['free_so2']
            post.total_so2 = cd['total_so2']

            post.is_star_review = cd['is_star_review']
            post.is_biodynamic = cd['is_biodynamic']
            post.is_organic = cd['is_organic']
            post.certified_by = cd['certified_by']
            post_old_status = post.status

            if cd['place_id']:
                place = Place.active.get(id=cd['place_id'])
                post.place = place

            if cd['is_parent_post']:
                Post.active.filter(
                    wine=post.wine,
                    type=PostTypeE.WINE,
                    is_parent_post=True
                ).exclude(id=id).update(is_parent_post=False)

            if cd['status'] != SpecialStatusE.DELETE:
                post.status = cd['status']

            if cd['status'] != PostStatusE.DRAFT:
                post.is_parent_post = cd['is_parent_post']

            if not post.yearly_data:
                post.yearly_data = {}

            if cd['year']:
                yr = cd['year']
                if post.is_parent_post:
                    ydata = {
                        'free_so2': cd['free_so2'],
                        'total_so2': cd['total_so2'],
                        'grape_variety': cd['grape_variety'],
                    }
                    post.yearly_data[yr] = ydata
                else:
                    pposts = Post.objects.filter(
                        wine=post.wine, is_parent_post=True
                    )
                    if pposts:
                        ppost = pposts[0]
                        if not ppost.yearly_data:
                            ppost.yearly_data = {}
                        if (
                            yr not in ppost.yearly_data or
                            empty_fields_in_yearly_data(
                                ppost.yearly_data[yr],
                                ['free_so2', 'total_so2', 'grape_variety']
                            )
                        ):
                            ydata = {
                                'free_so2': cd['free_so2'],
                                'total_so2': cd['total_so2'],
                                'grape_variety': cd['grape_variety'],
                            }
                            ppost.yearly_data[cd['year']] = ydata
                            ppost.save()
                            ppost.refresh_from_db()

            post.save()
            post.refresh_from_db()

            if cd['winemaker']:
                new_winemaker = Winemaker.active.get(id=cd['winemaker'].id)
                post.wine.winemaker = new_winemaker

            # blocked (commented out) on Bretin's request at 12. Dec 2017
            # post.wine.winemaker.modified_time = dt.datetime.now()
            # post.wine.winemaker.save()
            # post.wine.winemaker.refresh_from_db()

            if images:
                post_image = PostImage(image_file=images[0], post=post)
                post_image.save()
                post.main_image = post_image
                post.save()
                post.refresh_from_db()

            if wine_images:
                wine_image = WineImage(
                    image_file=wine_images[0], wine=post.wine
                )
                wine_image.save()
                post.wine.main_image = wine_image
                post.wine.save()
                post.wine.refresh_from_db()

            if ref_images:
                ref_image = create_vuforia_image_from_file(
                    request.user, ref_images[0], post.wine, post
                )
                post.wine.ref_image = ref_image
                post.ref_image = ref_image
                post.save()
                post.refresh_from_db()

            create_vuforia_images_for_post_and_wine(post)

            if post.status == PostStatusE.PUBLISHED:
                post.publish(
                    validated_by=request.user, update_published_time=(post_old_status != PostStatusE.PUBLISHED)
                )
            elif post.status == PostStatusE.DRAFT:
                post.unpublish(modifier_user=request.user)
            elif post.status == PostStatusE.REFUSED or post.status == PostStatusE.HIDDEN:
                post.refuse(modifier_user=request.user)
            elif post.status == PostStatusE.IN_DOUBT:
                post.set_in_doubt(modifier_user=request.user)
            elif post.status == PostStatusE.BIO_ORGANIC:
                post.set_bio_organic(modifier_user=request.user)
            elif post.status == PostStatusE.TO_INVESTIGATE:
                post.set_to_investigate(modifier_user=request.user)

            post.refresh_from_db()

            # if not was_star_review and post.is_star_review:
            #     SenderNotifier().send_star_review_on_winepost(post)

            # if post.status == PostStatusE.HIDDEN:
            #     return redirect('list_wineposts')

            data_in = {
                'name': post.wine.name,
                'name_short': post.wine.name_short,
                'domain': WinepostHelper.get_winepost_domain(post),
                'designation': post.wine.designation,
                'grape_variety': post.grape_variety,
                'color': post.wine.color,
                'is_sparkling': post.wine.is_sparkling,
                'is_star_review': post.is_star_review,
                'team_comments': post.team_comments,
                'is_parent_post': post.is_parent_post if post.status != PostStatusE.DRAFT else False,
                'year': post.wine_year,
                'winemaker': post.wine.winemaker_id,
                # 'region': post.wine.region,
                'description': post.description,
                'geolocation': post.place.name if post.place else None,
                'place_id': post.place.id if post.place else None,
                'original_winemaker_name': WinemakerHelper.get_original_name(winemaker=post.wine.winemaker),
                'wine_trade': post.wine_trade,
                'free_so2': post.free_so2,
                'total_so2': post.total_so2,
                'is_biodynamic': post.is_biodynamic,
                'is_organic': post.is_organic,
                'certified_by': post.certified_by,
            }

            if post.is_archived:
                data_in['status'] = SpecialStatusE.DELETE
            else:
                data_in['status'] = post.status

            form = AdminWinePostForm(data=data_in)
    else:
        form = AdminWinePostForm(data=data_in)

    some_parent_post = Post.active.filter(
        wine=post.wine, type=PostTypeE.WINE, is_parent_post=True
    ).exclude(id=id).first()

    if some_parent_post:
        log.debug("WINEPOST_VIEW - SOME_PARENT_POST: %s" % some_parent_post.id)
    else:
        log.debug("WINEPOST_VIEW - NO PARENT POST ")

    some_star_review = Post.active.filter(
        wine=post.wine, type=PostTypeE.WINE, is_star_review=True
    ).exclude(id=id).first()

    if post.last_modifier:
        context["saved_by"] = post.last_modifier
        context["saved_at"] = post.modified_time
    else:
        context["saved_by"] = post.author
        context["saved_at"] = post.created_time

    context['is_draft'] = True if post.status == PostStatusE.DRAFT else False
    context["form"] = form
    context["post"] = post
    if post.wine.ref_image_id:
        post_vuforia_url = reverse('get_vuforia_image_ajax', kwargs={"pid": post.wine.ref_image_id})
        context["post_vuforia_url"] = get_url_with_random_suffix(post_vuforia_url)
    else:
        context["post_vuforia_url"] = ""

    context["is_new"] = False
    context['add_wm_url'] = add_wm_url

    context['current_status'] = PostStatusE.names[post.status] if post.status in PostStatusE.names else None
    context["action_url"] = reverse('edit_winepost', args=[id])
    context["some_parent_post"] = some_parent_post
    context["some_star_review"] = some_star_review
    context["geolocation_url"] = reverse(
        'edit_place',
        args=[post.place.id]
    ) if post.place else ""
    context["geolocation_title"] = post.place.name if post.place else ""

    post_title = post.wine.name

    context["pdg_title"] = post_title
    context["pdg_author"] = post.author
    context["pdg_created_at"] = post.created_time
    context["pdg_validated_at"] = post.validated_at
    context["pdg_validated_by"] = post.validated_by

    context["pdg_options"] = WinepostHelper.get_pdg_options()

    context['wm_natural'] = is_natural_winemaker
    context['post_natural'] = is_natural_post
    context['el_style_natural'] = 'display: inline;' if is_natural_post else 'display: none;'
    context['el_style_other'] = 'display: none;' if is_natural_post else 'display: inline;'

    context['el_style_natural_pp'] = 'display: block;' if is_natural_post else 'display: none;'
    context['el_style_other_pp'] = 'display: none;' if is_natural_post else 'display: block;'

    vrt = post.get_vuf_rating_tracking()
    context['rating'] = '{}/6'.format(int(vrt + 1)) if vrt is not None else 'n.a.'

    context['is_scanned'] = post.is_scanned
    context['display_with_three_images'] = bool(post.is_parent_post and post.status != PostStatusE.DRAFT)

    # get active winepost url, can be changed since 'is_parent' of the post can be changed
    active_url_name = WinepostHelper.get_active_endpoint_url_name(post, is_natural=is_natural_winemaker)
    bc_path = WinepostHelper.get_bc_path(post, active_url_name)
    context = get_c(request=request, active=active_url_name, path=None, bc_path_alt=bc_path, old_c=context)
    return render(request, "edit/winepost.html", context)
