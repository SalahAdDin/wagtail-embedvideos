from django.apps import AppConfig
from django.utils.translation import ugettext_lazy as _


class WagtailEmbedVideosAppConfig(AppConfig):
    name = 'wagtail_embed_videos'
    label = 'wagtail_embed_videos'
    verbose_name = _("Wagtail Embed Videos")
