import json

try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse

from django.shortcuts import get_object_or_404, render

from wagtail.admin.modal_workflow import render_modal_workflow
from wagtail.admin.forms import SearchForm
from wagtail.admin.utils import PermissionPolicyChecker
from wagtail.admin.utils import popular_tags_for_model
from wagtail.core import hooks
from wagtail.core.models import Collection
from wagtail.search import index as search_index
from wagtail.utils.pagination import paginate

from embed_video.backends import detect_backend

from wagtail_embed_videos import get_embed_video_model
from wagtail_embed_videos.formats import get_video_format
from wagtail_embed_videos.forms import get_embed_video_form, EmbedVideoInsertionForm
# from wagtail_embed_videos.formats import get_embed_video_format
from wagtail_embed_videos.permissions import permission_policy

permission_checker = PermissionPolicyChecker(permission_policy)


def get_embed_video_json(embed_video):
    """
    helper function: given an embed video, return the json to pass back to the
    embed video chooser panel
    """
    if embed_video.thumbnail:
        preview_embed_video = embed_video.thumbnail.get_rendition('max-130x100').url
    else:
        preview_embed_video = detect_backend(embed_video.url).get_thumbnail_url()

    return json.dumps({
        'id': embed_video.id,
        'edit_link': reverse('wagtail_embed_videos:edit', args=(embed_video.id,)),
        'title': embed_video.title,
        'preview': {
            'url': preview_embed_video,
            'width': embed_video.thumbnail.width,
            'height': embed_video.thumbnail.height,
        }
    })


def chooser(request):
    EmbedVideo = get_embed_video_model()

    if permission_policy.user_has_permission(request.user, 'add'):
        EmbedVideoForm = get_embed_video_form(EmbedVideo)
        uploadform = EmbedVideoForm(user=request.user)
    else:
        uploadform = None

    embed_videos = EmbedVideo.objects.order_by('-created_at')

    # TODO: Make test for this functionality
    # allow hooks to modify the queryset
    for hook in hooks.get_hooks('construct_embed_video_chooser_queryset'):
        embed_videos = hook(embed_videos, request)

    q = None
    if (
                            'q' in request.GET or 'p' in request.GET or 'tag' in request.GET or
                    'collection_id' in request.GET
    ):
        collection_id = request.GET.get('collection_id')
        if collection_id:
            embed_videos = embed_videos.filter(collection=collection_id)

        searchform = SearchForm(request.GET)
        if searchform.is_valid():
            q = searchform.cleaned_data['q']

            embed_videos = embed_videos.search(q)
            is_searching = True

        else:
            is_searching = False

            tag_name = request.GET.get('tag')
            if tag_name:
                embed_videos = embed_videos.filter(tags__name=tag_name)

        paginator, embed_videos = paginate(request, embed_videos, per_page=12)

        return render(request, "wagtail_embed_videos/chooser/results.html", {
            'embed_videos': embed_videos,
            'is_searching': is_searching,
            'query_string': q,
            'will_select_format': request.GET.get('select_format')
        })
    else:
        searchform = SearchForm()

        collections = Collection.objects.all()
        if len(collections) < 2:
            collections = None

        paginator, embed_videos = paginate(request, embed_videos, per_page=12)

        return render_modal_workflow(
            request,
            'wagtail_embed_videos/chooser/chooser.html',
            'wagtail_embed_videos/chooser/chooser.js',
            {
                'embed_videos': embed_videos,
                'uploadform': uploadform,
                'searchform': searchform,
                'is_searching': False,
                'query_string': q,
                'will_select_format': request.GET.get('select_format'),
                'popular_tags': popular_tags_for_model(EmbedVideo),
                'collections': collections,
            }
        )


def embed_video_chosen(request, embed_video_id):
    embed_video = get_object_or_404(get_embed_video_model(), id=embed_video_id)

    return render_modal_workflow(
        request,
        None,
        'wagtail_embed_videos/chooser/embed_video_chosen.js',
        {'embed_video_json': get_embed_video_json(embed_video)}
    )


@permission_checker.require('add')
def chooser_upload(request):
    EmbedVideo = get_embed_video_model()
    EmbedVideoForm = get_embed_video_form(EmbedVideo)

    searchform = SearchForm()

    if request.POST:
        embed_video = EmbedVideo(uploaded_by_user=request.user)
        form = EmbedVideoForm(request.POST, request.FILES, instance=embed_video, user=request.user)

        if form.is_valid():
            form.save()

            # Reindex the video to make sure all tags are indexed
            search_index.insert_or_update_object(embed_video)

            if request.GET.get('select_format'):
                form = EmbedVideoInsertionForm(initial={'alt_text': embed_video.default_alt_text})
                return render_modal_workflow(
                    request,
                    'wagtail_embed_videos/chooser/select_format.html',
                    'wagtail_embed_videos/chooser/select_format.js',
                    {'embed_video': embed_video, 'form': form}
                )
            # not specifying a format; return the embed video details now
            else:
                return render_modal_workflow(
                    request,
                    None,
                    'wagtail_embed_videos/chooser/embed_video_chosen.js',
                    {'embed_video_json': get_embed_video_json(embed_video)}
                )
    else:
        form = EmbedVideoForm(user=request.user)

    embed_videos = EmbedVideo.objects.order_by('-created_at')
    paginator, images = paginate(request, embed_videos, per_page=12)

    return render_modal_workflow(
        request,
        'wagtail_embed_videos/chooser/chooser.html',
        'wagtail_embed_videos/chooser/chooser.js',
        {'embed_videos': embed_videos, 'uploadform': form, 'searchform': searchform}
    )


def chooser_select_format(request, embed_video_id):
    embed_video = get_object_or_404(get_embed_video_model(), id=embed_video_id)
    print(embed_video)

    if request.POST:
        form = EmbedVideoInsertionForm(request.POST, initial={'alt_text': embed_video.default_alt_text})

        if form.is_valid():
            format = get_video_format(form.cleaned_data['format'])
            preview_embed_video = detect_backend(embed_video.url).get_thumbnail_url()

            video_json = json.dumps({
                'id': embed_video.id,
                'title': embed_video.title,
                'format': format.name,
                'alt': form.cleaned_data['alt_text'],
                'class': format.classnames,
                'edit_link': reverse('wagtail_embed_videos:edit', args=(embed_video.id,)),
                'preview': {
                    'url': preview_embed_video,
                    'width': embed_video.thumbnail.width,
                    'height': embed_video.thumbnail.height,
                },
                'html': format.video_to_editor_html(embed_video, form.cleaned_data['alt_text']),
            })

            print(video_json)

            return render_modal_workflow(
                request,
                None,
                'wagtail_embed_videos/chooser/embed_video_chosen.js',
                {'embed_video_json': video_json}
            )
    else:
        initial = {'alt_text': embed_video.default_alt_text}
        initial.update(request.GET.dict())
        form = EmbedVideoInsertionForm(initial=initial)

    return render_modal_workflow(
        request,
        'wagtail_embed_videos/chooser/select_format.html',
        'wagtail_embed_videos/chooser/select_format.js',
        {'embed_video': embed_video, 'form': form}
    )
