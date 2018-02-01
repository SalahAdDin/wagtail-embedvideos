(function () {
    (function ($) {
        return $.widget('IKS.halloembedvideos', {
            options: {
                uuid: '',
                editable: null
            },
            populateToolbar: function (toolbar) {
                var button, widget;

                widget = this;
                button = $('<span class="' + this.widgetName + '"></span>');
                button.hallobutton({
                    uuid: this.options.uuid,
                    editable: this.options.editable,
                    label: 'Videos',
                    icon: 'icon-media',
                    command: null
                });
                toolbar.append(button);
                return button.on('click', function (event) {
                    var insertionPoint, lastSelection;

                    lastSelection = widget.options.editable.getSelection();
                    insertionPoint = $(lastSelection.endContainer).parentsUntil('.richtext').last();
                    return ModalWorkflow({
                        url: window.chooserUrls.embedVideoChooser + '?select_format=true',
                        responses: {
                            embedVideoChosen: function (embedVideoData) {
                                var elem;

                                elem = $(embedVideoData.html).get(0);
                                lastSelection.insertNode(elem);
                                if (elem.getAttribute('contenteditable') === 'false') {
                                    insertRichTextDeleteControl(elem);
                                }

                                return widget.options.editable.element.trigger('change');
                            }
                        }
                    });
                });
            }
        });
    })(jQuery);

}).call(this);
