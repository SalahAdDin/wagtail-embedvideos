from wagtail.admin.edit_handlers import BaseChooserPanel
from .widgets import AdminEmbedVideoChooser


class EmbedVideoChooserPanel(BaseChooserPanel):
    object_type_name = "embed_video"

    def widget_overrides(cls):
        return {cls.field_name: AdminEmbedVideoChooser}

