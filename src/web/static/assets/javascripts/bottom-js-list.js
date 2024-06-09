
$(document).ready(function ($) {
    // delegate calls to data-toggle="lightbox"
    $(document).delegate('*[data-toggle="lightbox"]:not([data-gallery="navigateTo"])', 'click', function(event) {
        event.preventDefault();
        return $(this).ekkoLightbox({
            onShown: function() {
                if (window.console) {
                    return console.log('onShown event fired');
                }
            },
            onContentLoaded: function() {
                if (window.console) {
                    return console.log('onContentLoaded event fired');
                }
            },
            onNavigate: function(direction, itemIndex) {
                if (window.console) {
                    return console.log('Navigating '+direction+'. Current item: '+itemIndex);
                }
            }
        });
    });

    //Programatically call
    $('#open-image').click(function (e) {
        e.preventDefault();
        $(this).ekkoLightbox();
    });
    $('#open-youtube').click(function (e) {
        e.preventDefault();
        $(this).ekkoLightbox();
    });

    $(document).delegate('*[data-gallery="navigateTo"]', 'click', function(event) {
        event.preventDefault();
        return $(this).ekkoLightbox({
            onShown: function() {
                var lb = this;
                $(lb.modal_content).on('click', '.modal-footer a#jumpit', function(e) {
                    e.preventDefault();
                    lb.navigateTo(2);
                });
                $(lb.modal_content).on('click', '.modal-footer a#closeit', function(e) {
                    e.preventDefault();
                    lb.close();
                });
            }
        });
    });

});
