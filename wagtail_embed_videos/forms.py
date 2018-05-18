from django import forms
from django.forms.models import modelform_factory
from django.utils.translation import ugettext as _

from wagtail.admin import widgets
from wagtail.admin.forms import BaseCollectionMemberForm
from wagtail.admin.forms import collection_member_permission_formset_factory
from wagtail.images.edit_handlers import AdminImageChooser
from wagtail.images.formats import get_image_formats

from wagtail_embed_videos.models import EmbedVideo

from .permissions import permission_policy as embed_video_permission_policy


class BaseEmbedVideoForm(BaseCollectionMemberForm):
    permission_policy = embed_video_permission_policy


def get_embed_video_form(model):
    fields = model.admin_form_fields

    if 'collection' not in fields:
        # force addition of the 'collection' field, because leaving it out can
        # cause dubious results when multiple collections exist (e.g adding the
        # document to the root collection where the user may not have permission) -
        # and when only one collection exists, it will get hidden anyway.
        fields = list(fields) + ['collection']

    return modelform_factory(
        model,
        form=BaseEmbedVideoForm,
        fields=fields,
        # formfield_callback=formfield_for_dbfield,
        widgets={
            'tags': widgets.AdminTagWidget,
            'thumbnail': AdminImageChooser,
        })


class EmbedVideoInsertionForm(forms.Form):
    """
    Form for selecting parameters of the image (e.g. format) prior to insertion
    into a rich text area
    """
    format = forms.ChoiceField(
        choices=[(format.name, format.label) for format in get_image_formats()],
        widget=forms.RadioSelect
    )
    alt_text = forms.CharField()


GroupEmbedVideoPermissionFormSet = collection_member_permission_formset_factory(
    EmbedVideo,
    [
        ('add_embedvideo', _("Add"), _("Add/edit embed videos you own")),
        ('change_embedvideo', _("Edit"), _("Edit any embed video")),
    ],
    'wagtail_embed_videos/permissions/includes/video_permissions_formset.html'
)
