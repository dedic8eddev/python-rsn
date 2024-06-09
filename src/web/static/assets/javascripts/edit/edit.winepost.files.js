init.push(function () {
    image_manager_wm_files = new ImageManager($("#container-other-files"), {
        b_sortable: null,
        temp_image_ordering_field: null,
        url_current_images : url_current_wm_files_ajax,
        url_delete_image : url_wm_file_delete_ajax,
        image_identifier_xhr_field: "id",
        remove_btn_selector: 'a.remover',

        callback: function(){
        }
    });
});


init.push(function () {
    b_dropzone_wm_files = $("#dropzonejs-wm-files").dropzone({
        url: url_wm_file_upload_ajax,
        dictFileTooBig: "Error!\nFile file is bigger than {{maxFilesize}} K.O",

        sending: function(file, xhr, formData){
            $(".jq-growl-error-button-container").hide();
            formData.append('parent_id', winepost_id);
        },

        error: function(data, message) {
            console.log("MAX FILE SIZE", this.options.maxFilesize);
            console.log("ERROR", data);
            console.log("ERROR message", message);
            $.growl.error({ "message": message });
//            $("#spinner").hide();
            //            $(".jq-growl-error-button-container").show();
            //            $('#jq-growl-error').unbind('click');
            //            $('#jq-growl-error').click(function () {
            //                $.growl.error({ "message": message });
            //                $(".jq-growl-error-button-container").hide();
            //            });
        },

        complete: function(file){
            this.removeFile(file);
            var no_files = Dropzone.forElement('#dropzonejs-wm-files').getQueuedFiles().length
            if (no_files < 1) {
                $("#spinner").hide();
            }
        },

        success: function(file, response){
            // image_manager.refreshImagesWithHtml(response);
            image_manager_wm_files.refreshImages();
            // image_manager.handleImages();
        },

        //        totaluploadprogress: function(a,b,c) {
        //            if (a==100 && b == 0 && c == 0) {
        //                $("#spinner").hide();
        //                $("#wl-refresh-button").show();
        //            }
        //        },

        paramName: "file", // The name that will be used to transfer the file
        maxFilesize: 100, // MB

        addRemoveLinks : true,
        dictResponseError: "Can't upload file!",
        dictDefaultMessage: "Upload files",
        //  When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. See below for more information on handling queues.
//        autoProcessQueue: false,
        thumbnailWidth: 138,
        thumbnailHeight: 120,

        previewTemplate: ['<div class="col-sm-2">',
                            '<img data-dz-thumbnail /><span class="dz-nopreview">No preview</span>',
                            '<span class="error text-danger" data-dz-errormessage>',
                            '<div class="progress progress-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">',
                                '<div class="dz-success-mark"><span class="glyphicon glyphicon-ok-circle"></span></div>',
                                '<div class="dz-error-mark"><span class="glyphicon glyphicon-ban-circle"></span></div>',
                                '<div class="progress-bar progress-bar-success" style="width: 0%;" data-dz-uploadprogress></div>',
                            '</div>',

                        '</div>' ].join(),

        resize: function(file) {
            var info = { srcX: 0, srcY: 0, srcWidth: file.width, srcHeight: file.height },
                srcRatio = file.width / file.height;
            if (file.height > this.options.thumbnailHeight || file.width > this.options.thumbnailWidth) {
                info.trgHeight = this.options.thumbnailHeight;
                info.trgWidth = info.trgHeight * srcRatio;
                if (info.trgWidth > this.options.thumbnailWidth) {
                    info.trgWidth = this.options.thumbnailWidth;
                    info.trgHeight = info.trgWidth / srcRatio;
                }
            } else {
                info.trgHeight = file.height;
                info.trgWidth = file.width;
            }
            return info;
        }
    });
});


$(document).ready(function () {
//    $('#toggle-all').click(function() {
//        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
//    });

    $('#styled-finputs-example').pixelFileInput({ placeholder: 'No file selected...' });

    // delegate calls to data-toggle="lightbox"
    // $(document).delegate('*[data-toggle="lightbox"]:not([data-gallery="navigateTo"])', 'click', function(event) {
    //     event.preventDefault();
    //     return $(this).ekkoLightbox({
    //         onShown: function() {
    //             if (window.console) {
    //                 return console.log('onShown event fired');
    //             }
    //         },
    //         onContentLoaded: function() {
    //             if (window.console) {
    //                 return console.log('onContentLoaded event fired');
    //             }
    //         },
    //         onNavigate: function(direction, itemIndex) {
    //             if (window.console) {
    //                 return console.log('Navigating '+direction+'. Current item: '+itemIndex);
    //             }
    //         }
    //     });
    // });

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

    init.push(function () {
        //$('#styled-finputs-example').pixelFileInput({ placeholder: 'No file selected...' });
        $('#id_image').pixelFileInput({ placeholder: 'No file selected...' });
        $('#id_wine_image').pixelFileInput({ placeholder: 'No file selected...' });
        $('#id_ref_image').pixelFileInput({ placeholder: 'No file selected...' });
    });

});
