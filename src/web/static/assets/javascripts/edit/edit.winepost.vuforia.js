// ==== PIXIE ====
init.push(function(){
    if($("#ref-img").length != 0) {

        var image_url_test = $("#ref-img").attr('src');
        if(image_url_test !=undefined && image_url_test !=null && image_url_test != '' &&
                image_url_test.indexOf('/img/missing.gif') == -1 ) {
            var image_url = image_url_test;
            var filename = get_basename(image_url);
        }else {
            var image_url = '';
            var filename = 'new-image.png';
        }

        pixie = new Pixie({
            image: image_url,
            blankCanvasSize: {
                width: 640,
                height: 680
            },

            urls: {
               base: '/static/assets/pixie/',
               assets: '/static/assets/pixie/'
            },
            languages: {
                active: 'english',
                custom: {
                    english: {open: "Upload"}
                }
            },
            ui: {
                allowEditorClose: true,
                toolbar: {
                    hideOpenButton: false,
                    hideCloseButton: false,
                    openButtonAction: function() {
                        pixie.getTool('importTool').openUploadDialog({'backgroundImage': true});
                    }
                },
                openImageDialog: false,
                mode: 'overlay'
            },

            onLoad: function() {
                //                var cropTool = pixie.getTool('crop');
                //                cropTool.apply({width: 100, height: 100, left: 0, top: 50});
            },
            onSave: function(data, name) {
                pixie.http().post(
                    url_upload_winepost_ref_image_ajax,
                    {
                        editor_name: name,
                        name: filename,
                        data: data,
                        parent_id: winepost_id
                    }
                ).subscribe(function(response) {
                    if(response.status == 'ok' && response.url != undefined && response.url != null &&
                            response.url != '') {
                        var data_url = response.url + '?' + new Date().getTime()
                        $("#ref-img").prop('src', data_url);
                        pixie.resetEditor('image', data_url);
                        alert("Image has been saved.");
                    }
                });
            }
        });

        $("#open_photo_editor").click(function(){
            pixie.resetAndOpenEditor('image', document.querySelector('#ref-img'));
            return false;
        });

        $("#open_photo_editor_blank").click(function(){
            pixie.resetAndOpenEditor('image', src_blank_canvas);
            return false;
        });

        $(".set-as-vuforia").click(function(){
            var what = $(this).data('what');
            $.ajax({
                type: "POST",
                dataType: "json",
                url: url_set_as_vuforia_ajax,
                data: {
                    "winepost_id": winepost_id,
                    "what": what
                },
                success: function(data) {
                    if(data.status == 'OK') {
                        if(data.url != undefined && data.url != null && data.url != '') {
                            alert("Image has been set as Vuforia image");
                            var data_url = data.url + '?' + new Date().getTime()
                            $("#ref-img").prop('src', data_url);
                            pixie.resetEditor('image', data_url);
                        } else {
                            alert("No image to be set. Upload one first.");
                        }
                    } else {
                        alert("Image could not be set as Vuforia image");
                    }
                },
                error: function(data){
                    console.warn(data);
                }
            });

            return false;
        });
    }
});
// ==== /PIXIE ====


function move_to_vuforia_from_list(post_id, what) {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: url_set_as_vuforia_ajax,
        data: {
            "winepost_id": post_id,
            "what": what
        },
        success: function(data) {
            if(data.status == 'OK') {
                if(data.url != undefined && data.url != null && data.url != '') {
                    b_datatable_reviews.refreshList();

                    alert("Image has been set as Vuforia image");
                    var data_url = data.url + '?' + new Date().getTime()
                    $("#ref-img").prop('src', data_url);
                    pixie.resetEditor('image', data_url);
                } else {
                    alert("No image to be set. Upload one first.");
                }
            } else {
                alert("Image could not be set as Vuforia image");
            }
        },
        error: function(data){
            console.warn(data);
        }
    });

}


function refresh_vuforia_image() {
    $.ajax({
        type: "POST",
        dataType: "json",
        url: url_refresh_vuforia_image,
        data: {
            "winepost_id": winepost_id
        },
        success: function(data) {
            if(data.status == 'OK') {
                if(data.url != undefined && data.url != null && data.url != '') {
                    alert("Image has been set for re-upload to Vuforia, it would be "+
                        "taken there by the background script soon.");
                    var data_url = data.url + '?' + new Date().getTime()
                    $("#ref-img").prop('src', data_url);
                    pixie.resetEditor('image', data_url);
                } else {
                    alert("No image to be re-uploaded to Vuforia. Upload one first.");
                }
            } else {
                alert("Image could not be re-uploaded to Vuforia.");
            }
        },
        error: function(data){
            console.warn(data);
        }
    });

}
