from draftjs_exporter.dom import DOM

from wagtail.admin.rich_text.converters import editor_html
from wagtail.admin.rich_text.converters.contentstate_models import Entity
from wagtail.admin.rich_text.converters.html_to_contentstate import AtomicBlockEntityElementHandler

from wagtail_embed_videos import get_embed_video_model


# Front-end conversion

def video_embedtype_handler(attrs):
    """
    Given a dict of attributes from the <embed> tag, return the real HTML
    representation for use on the front-end.
    """
    Video = get_embed_video_model()
    try:
        video = Video.objects.get(id=attrs['id'])
    except Video.DoesNotExist:
        return "<video>"

    video_format = get_video_format(attrs['format'])
    return video_format.video_to_html(video, attrs.get('alt', ''))


# hallo.js / editor-html conversion

class VideoEmbedHandler:
    """
    VideoEmbedHandler will be invoked whenever we encounter an element in HTML content
    with an attribute of data-embedtype="video". The resulting element in the database
    representation will be:
    <embed embedtype="video" id="42" format="thumb" alt="some custom alt text">
    """

    @staticmethod
    def get_db_attributes(tag):
        """
        Given a tag that we've identified as an video embed (because it has a
        data-embedtype="video" attribute), return a dict of the attributes we should
        have on the resulting <embed> element.
        """
        return {
            'id': tag['data-id'],
            'format': tag['data-format'],
            'alt': tag['data-alt'],
        }

    @staticmethod
    def expand_db_attributes(attrs):
        """
        Given a dict of attributes from the <embed> tag, return the real HTML
        representation for use within the editor.
        """
        Video = get_embed_video_model()
        try:
            video = Video.objects.get(id=attrs['id'])
        except Video.DoesNotExist:
            return "<video>"

        video_format = get_video_format(attrs['format'])  # TODO: What's about this?

        return video_format.video_to_editor_html(video, attrs.get('alt', ''))


EditorHTMLEmbedVideoConversionRule = [
    editor_html.EmbedTypeRule('video', VideoEmbedHandler)
]


# draft.js / contentstate conversion

def video_entity(props):
    """
    Helper to construct elements of the form
    <embed alt="Right-aligned video" embedtype="video" format="right" id="1"/>
    when converting from contentstate data
    """
    return DOM.create_element('embed', {
        'embedtype': 'video',
        'format': props.get('format'),
        'id': props.get('id'),
        'alt': props.get('alt'),
    })


class VideoElementHandler(AtomicBlockEntityElementHandler):
    """
    Rule for building an video entity when converting from database representation
    to contentstate
    """

    def create_entity(self, name, attrs, state, contentstate):
        Video = get_embed_video_model()
        try:
            video = Video.objects.get(id=attrs['id'])
            video_format = get_video_format(attrs['format'])
            src = video.url
        except Video.DoesNotExist:
            src = ''

        return Entity('VIDEO', 'IMMUTABLE', {
            'id': attrs['id'],
            'src': src,
            'alt': attrs.get('alt'),
            'format': attrs['format']
        })


ContentstateEmbedVideoConversionRule = {
    'from_database_format': {
        'embed[embedtype="video"]': VideoElementHandler(),
    },
    'to_database_format': {
        'entity_decorators': {'VIDEO': video_entity}
    }
}
