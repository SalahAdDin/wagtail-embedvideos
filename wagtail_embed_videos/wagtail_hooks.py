from django.conf import settings
from django.conf.urls import include, url
from django.contrib.staticfiles.templatetags.staticfiles import static

try:
    from django.urls import reverse
except ImportError:  # Django<2.0
    from django.core.urlresolvers import reverse

from django.utils.html import format_html, format_html_join
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ungettext

from wagtail.admin.menu import MenuItem
from wagtail.admin.search import SearchArea
from wagtail.wagtailadmin.rich_text import HalloPlugin
from wagtail.admin.site_summary import SummaryItem
from wagtail.core import hooks

from wagtail_embed_videos import admin_urls
from wagtail_embed_videos.api.admin.endpoints import EmbedVideosAdminAPIEndpoint
from wagtail_embed_videos.forms import GroupEmbedVideoPermissionFormSet
from wagtail_embed_videos import get_embed_video_model
from wagtail_embed_videos.permissions import permission_policy


@hooks.register('register_admin_urls')
def register_admin_urls():
    return [
        url(r'^embed_videos/', include(admin_urls, namespace='wagtail_embed_videos')),
    ]


@hooks.register('construct_admin_api')
def construct_admin_api(router):
    router.register_endpoint('embed_videos', EmbedVideosAdminAPIEndpoint)


class EmbedVideosMenuItem(MenuItem):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_menu_item')
def register_embed_videos_menu_item():
    return EmbedVideosMenuItem(
        _('Videos'),
        reverse('wagtail_embed_videos:index'),
        name='embed_videos',
        classnames='icon icon-media',
        order=301
    )


@hooks.register('insert_editor_js')
def editor_js():
    js_files = [
        static('wagtail_embed_videos/js/embed-video-chooser.js'),
    ]
    js_includes = format_html_join(
        '\n', '<script src="{0}"></script>',
        ((filename,) for filename in js_files)
    )
    return js_includes + format_html(
        """
        <script>
            window.chooserUrls.embedVideoChooser = '{0}';
            registerHalloPlugin('halloembedvideos');
        </script>
        """,
        reverse('wagtail_embed_videos:chooser')
    )


@hooks.register('register_rich_text_features')
def register_embed_videos_feature(features):
    features.register_editor_plugin(
        'hallo', 'embedvideos',
        HalloPlugin(
            name='halloembedvideos',
            js=['wagtail_embed_videos/js/hallo-plugins/hallo-embedvideos.js'],
        )
    )
    features.default_features.append('embedvideos')


class EmbedVideosSummaryItem(SummaryItem):
    order = 800
    template = 'wagtail_embed_videos/homepage/site_summary_videos.html'

    def get_context(self):
        return {
            'total_videos': get_embed_video_model().objects.count(),
        }

    def is_shown(self):
        return permission_policy.user_has_any_permission(
            self.request.user, ['add', 'change', 'delete']
        )


@hooks.register('construct_homepage_summary_items')
def add_embed_videos_summary_item(request, items):
    items.append(EmbedVideosSummaryItem(request))


class EmbedVideosSearchArea(SearchArea):
    def is_shown(self, request):
        return permission_policy.user_has_any_permission(
            request.user, ['add', 'change', 'delete']
        )


@hooks.register('register_admin_search_area')
def register_embed_videos_search_area():
    return EmbedVideosSearchArea(
        _('Videos'),
        reverse('wagtail_embed_videos:index'),
        name='embed_videos',
        classnames='icon icon-media',
        order=600
    )


@hooks.register('register_group_permission_panel')
def register_embed_video_permissions_panel():
    return GroupEmbedVideoPermissionFormSet


@hooks.register('describe_collection_contents')
def describe_collection_docs(collection):
    embed_videos_count = get_embed_video_model().objects.filter(collection=collection).count()
    if embed_videos_count:
        url = reverse('wagtail_embed_videos:index') + ('?collection_id=%d' % collection.id)
        return {
            'count': embed_videos_count,
            'count_text': ungettext(
                "%(count)s video",
                "%(count)s videos",
                embed_videos_count
            ) % {'count': embed_videos_count},
            'url': url,
        }
