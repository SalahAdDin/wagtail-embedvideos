function createEmbedVideoChooser(id) {
    var chooserElement = $('#' + id + '-chooser');
    var previewEmbedVideo = chooserElement.find('.preview-image img');
    var input = $('#' + id);
    var editLink = chooserElement.find('.edit-link');

    $('.action-choose', chooserElement).click(function() {
        ModalWorkflow({
            'url': window.chooserUrls.embedVideoChooser,
            'responses': {
                'embedVideoChosen': function(embedVideoData) {
                    input.val(embedVideoData.id);
                    previewEmbedVideo.attr({
                        src: embedVideoData.preview.url,
                        width: embedVideoData.preview.width,
                        height: embedVideoData.preview.height,
                        alt: embedVideoData.title
                    });
                    chooserElement.removeClass('blank');
                    editLink.attr('href', embedVideoData.edit_link);
                }
            }
        });
    });

    $('.action-clear', chooserElement).on('click', function() {
        input.val('');
        chooserElement.addClass('blank');
    });
}
