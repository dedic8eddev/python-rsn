$(function () {
  $('[data-toggle="tooltip"]').tooltip();
});

$('.sticky-save').mouseenter(function(e){
  e.stopPropagation();
  $(this).stop().animate();
});

$('.sticky-save').mouseleave(function(e){
  $(this).fadeOut();
});

function handle_sticky_save(status){
  var $sticky = $('.sticky-save.' + status);
  $sticky.show();
  var timeout = setTimeout(function() {
    if (!$sticky.is(":hover")){
    $sticky.fadeOut();
  }
  }, 5000);
}

function get_dropzone_path(area) {
    area = area.toLowerCase();
    let dropzone_path = "#upload-wine-" + area;
    return dropzone_path;
}

function get_image_list_path(area) {
    area = area.toLowerCase();
    let list_path = '#' + area;
    return list_path;
}

function validate_image(element, teamImage) {
    let _fileExtensions = ["png", "jpg", "gif", "jpeg", "heic"];
    let image = $(element)[0].files[0];
    if (!image) {
        if (teamImage) show_hide_dropify(5, false);
        return 0;
    }
    let imageExtension = image.name.split('.').pop().toLowerCase();

    let error = image_error(teamImage);

    // Image extension validation
    if (_fileExtensions.includes(imageExtension) === false) {
        $(error.extensionError).slideDown("slow");
        $(error.sizeError).slideUp("slow");
        $(element).val("")
    } else {
        // Image size validation
        let picSize = image.size;
        if (!teamImage && picSize > 5000000) { // logo is too big
            $(error.sizeError).slideDown("slow");
            $(error.extensionError).slideUp("slow");
            $(element).val("")
        } else { // logo is OK
            $("#establishment-logo-removed").val("");
            if (!teamImage) $(error.sizeError).slideUp("slow");
            $(error.extensionError).slideUp("slow");
            return 0;

        }
    }
}

function image_error(team) {
    return {
        "extensionError": team ? "#extension-error-team" : "#extension-error-logo",
        "sizeError": "#size-error-logo"
    }
}

function add_image_name_attribute() {
    $(".dropify-render").eq(1).children().eq(0).attr("id-image", "establishment-logo");
}



function init_dropzones(url, token) {
    Dropzone.options.frontDropzone = dropzone_settings(url, token, 4, "FRONT");
    Dropzone.options.interiorDropzone = dropzone_settings(url, token, 4, "INTERIOR");
    Dropzone.options.atWorkDropzone = dropzone_settings(url, token, 4, "AT_WORK");
    Dropzone.options.teamDropzone = dropzone_settings(url, token, 1, "TEAM");
}

function dropzone_settings(url, token, maxFiles, imageName) {
    return {
        url: url,
        headers: {
            'X-CSRFToken': token
        },
        autoProcessQueue: true,
        uploadMultiple: true,
        paramName: imageName,
        maxFileSize: 5,
        maxFiles: maxFiles,
        parallelUploads: 4,
        addRemoveLinks: false,
        dictFileTooBig: "File size cannot be bigger than 5 MB",
        dictMaxFilesExceeded: "You can only upload up to 4 images per row",
        acceptedFiles: ".jpeg,.jpg,.png,.gif,.heic",
        error: function (xhr, status, error) {
            handle_sticky_save('error');
            console.log(error);
            return []
        },
        init: function () {
            let myDropzone = this;

            this.on("addedfiles", function (fileList) {
                let imageList = $(get_image_list_path(imageName));
                let imageListLength = imageList.children().length;
                if (imageListLength < 4) {
                    for (let i = 4 - imageListLength; i < fileList.length; i++) {
                        this.removeFile(fileList[i])
                    }
                } else {
                    Array.from(fileList).forEach(function (index, element) {
                        myDropzone.removeFile(index)
                    });
                    $("#" + imageName.toLowerCase() + "-error-edit").slideDown("slow");
                }

            });

            this.on('error', function (file, message) {
                if (message === "You can only upload up to 4 images per row") {
                    $("#" + imageName.toLowerCase() + "-error-edit").slideDown("slow");
                } else if (message === "You can't upload files of this type.") {
                    $("#" + imageName.toLowerCase() + "-error-file").slideDown("slow");
                }
                this.removeFile(file);
            });

            this.on("complete", function (file) {
                // after adding images
                let response = JSON.parse(file.xhr.response);
                if (file && file.status === "success" && !$.isEmptyObject(response)) {
                    let imageList = $(get_image_list_path(imageName));
                    let areaToUse = imageName.toLowerCase();
                    show_hide_dropzone(areaToUse);
                    let imageSrc = [JSON.parse(file.xhr.response).image];
                    let visibleImagesSrc = get_images_src(imageName);
                    // let imageWidth = get_image_width();

                    for (let i = 0; i < imageSrc[0].length; i++) {
                        let imgSrc = imageSrc[0][i];
                        if (!visibleImagesSrc.includes(imgSrc)) {
                            if (imageList.children().length === 0) imageList.append(generate_image([imgSrc], true));
                            else imageList.append(generate_image([imgSrc]));
                        }
                    }

                    $(imageList).sortable({
                        connectWith: imageList,
                        scroll: false,
                        axis: 'x'
                    });
                    // change_image_width(imageList, imageWidth);

                    $("#" + imageName.toLowerCase() + "-error-edit").slideUp("slow");
                    $("#" + imageName.toLowerCase() + "-error-file").slideUp("slow");
                    changed += 1;
                    show_hide_dropzone(areaToUse);
                }
                this.removeFile(file);
            });
        },
    };
}

function get_images_src(imageName) {
    let imageList = $(get_image_list_path(imageName));
    let imagesSrc = [];
    imageList.children().find("img").each(function (index, element) {
        imagesSrc.push($(element).attr("src"))
    });
    return imagesSrc;
}

function prepare_dropify() {
    let dropifyElements = $(".dropify-wrapper");
    let logoDropifyElement = dropifyElements.eq(1);
    let teamDropifyElement = dropifyElements.eq(5);
    let logoHasImage = logoDropifyElement.find('img').length !== 0;
    let teamHasImage = teamDropifyElement.find('img').length !== 0;

    show_hide_dropify(1, logoHasImage);
    show_hide_dropify(5, teamHasImage);

}

function show_hide_dropzone(area) {
    area = area.toLowerCase();
    let list_path = get_image_list_path(area);
    let dropzone_path = get_dropzone_path(area);
    let len_images = $(list_path).children().length;
    if (len_images < 4) {
        $(dropzone_path).show();
    } else {
        $(dropzone_path).hide();

    }
}


function show_hide_dropify(num, hide) {
    let dropifyElement = $(".dropify-wrapper").eq(num).find('.dropify-message');
    // let dropifyColumnElement = dropifyElement.parents().eq(0);
    // let padding = hide ? "15px" : "25px";
    // let border = hide ? "none" : "1px solid rgb(235, 235, 226)";

    if (hide) {
        dropifyElement.attr('style', 'display: none !important')
    }
    else {
        // dropifyElement.width(130);
        // dropifyElement.height(105);
        dropifyElement.attr('style', '');
    }

    // dropifyColumnElement.css("padding-left", padding);
    // dropifyElement.css("border", border);
}

function update_sortable_view() {
    $(".sortable.list").each(function (index, element) {
        $(element).sortable({
            connectWith: element,
            scroll: false,
            axis: 'x',
        });
    });
}

function render_establishment_images(token, url) {
    get_establishment_images("FRONT", token, url);
    get_establishment_images("INTERIOR", token, url);
    get_establishment_images("AT_WORK", token, url);
    get_establishment_images("TEAM", token, url);
}

function generate_image(data, addWidth) {
    let html = "";
    if (data.length > 0) {
        data.forEach(function (src) {
            // if (addWidth) html += "<li class=\"img-item ui-sortable-handle\" draggable=\"true\" role=\"option\" aria-grabbed=\"false\">"; // style=\"width: " + $(window).width() / 8 + "px\"
            html += "<li class=\"img-item ui-sortable-handle\" draggable=\"true\" role=\"option\" aria-grabbed=\"false\">";

            html += "<figure class=\"img-hov-zoomin\">" +
                "<img class=\"w-130px rounded\" src=\"" + src + "\" alt=\"...\">" +
                "</figure>" +
                "<button type=\"button\" class=\"btn btn-square btn-danger btn-delete\"><i class=\"fa fa-trash-o\"></i></button>" +
                "</li>"
        })
    }
    return html
}

function wait_until_style_is_loaded() {
    let images = $(".img-item.ui-sortable-handle");
    let logoImage = $(".dropify-wrapper.has-preview");
    changed = 0;

    if (logoImage.length === 0) return setTimeout(wait_until_style_is_loaded, 1000);
    if (images.length !== 0 && !images.attr('style')) return setTimeout(wait_until_style_is_loaded, 1000);

    images.each(function () {
        $(this).removeAttr('style')
    });

    $(".custom-preloader").fadeOut('slow'); // , change_images_width())
    prepare_dropify();
}


function wait_until_logo_is_rendered(previousSrc) {
    let renderDivChild = $("#input-file-now-custom-1").parent().find(".dropify-render").children();
    if (renderDivChild.length === 0) return setTimeout(wait_until_logo_is_rendered, 100);
    if (renderDivChild[0].src === previousSrc) return setTimeout(wait_until_logo_is_rendered, 100);

    let dropifyElement = $(".dropify-wrapper").eq(1).find('.dropify-message');
    let img = dropifyElement.siblings().eq(4).find('img');
    img.addClass('w-130px rounded')

    // set_single_dropify_dimensions();
}

function wait_until_team_is_rendered(previousSrc) {
    let renderDivChild = $("#input-file-now-custom-2").parent().find(".dropify-render").children();
    if (renderDivChild.length === 0) return setTimeout(wait_until_team_is_rendered, 100);
    if (renderDivChild[0].src === previousSrc) return setTimeout(wait_until_team_is_rendered, 100);

    let dropifyElement = $(".dropify-wrapper").eq(5).find('.dropify-message');
    let img = dropifyElement.siblings().eq(4).find('img');
    img.addClass('w-130px rounded')
}

function post_images(url, token) {
    let data = JSON.stringify(prepare_post_images_json());
    $.ajax({
        url: url,
        headers: {
            'X-CSRFToken': token
        },
        type: 'post',
        async: false,
        dataType: 'json',
        data: data,
        error: function (xhr, status, error) {
            console.log(xhr.responseText, status, error);
            return []
        }
    });
}

function prepare_images_src(idNaming, arr) {
    $(idNaming).find('img').each(function (index, element) {
        arr.push($(element).attr('src').split("/media/").pop())
    });
}

function prepare_post_images_json() {
    let frontImages = [];
    let interiorImages = [];
    let atWorkImages = [];

    return {
        'FRONT': frontImages,
        'INTERIOR': interiorImages,
        'AT_WORK': atWorkImages
    };
}


function get_establishment_images(area, token, url) {
   // $(".upload-wine").attr("style", "height:auto;");
    // $(get_dropzone_path(area)).attr("style", "height:auto;");
    let imageList = $(get_image_list_path(area));
    let data = {"area": area};
    $.ajax({
        url: url,
        headers: {
            'X-CSRFToken': token
        },
        type: 'post',
        async: false,
        dataType: 'json',
        data: data,
        success: function (data) {
            imageList.append(generate_image(data.result));
            show_hide_dropzone(area.toLowerCase());
        },
        error: function (xhr, status, error) {
            console.log(error);
            return []
        },
    });
}

function anchor_handler() {
    let anchorHash = window.location.href.toString();
    if (anchorHash.lastIndexOf('#') !== -1) {
        anchorHash = anchorHash.substr(anchorHash.lastIndexOf('#'));
        let anchorElement = $('a[href="' + anchorHash + '"]');
        if (anchorElement.length > 0) {
            anchorElement.trigger('click');
        }
    }
    $(".nav-link").on('click', function () {
        window.location.hash = this.name
    })
}

tinymce.init({
    selector: '#tinymce',
    inline: true,
    menubar: false,
    plugins:[],
    toolbar: [],
    init_instance_callback: function(editor) {
        var max = 195;
        editor.on('init', function(e) {
            console.log('The Editor has initialized.');
        });
        editor.on('keydown', function(e) {
            var content = tinymce.activeEditor.getContent({format : 'text'});   
            if (content.length >= max) {
              if (e.keyCode != 8)
                e.preventDefault();
            }
        });
        editor.on('keyup', function(e) {
            var content = tinymce.activeEditor.getContent({format : 'text'});   
            if (typeof callbackMax == 'function') {
                callbackMax(max - content.length);
            }
            $(".character_remaning").show();
            $("#remaining-caracteres").text(max - content.length);
            console.log(max - content.length)

            if(max - content.length <= 0){
                $(".character_remaning").addClass("text-danger");
                console.log("zero or less")
            }else{
                $(".character_remaning").removeClass("text-danger");
            }
            if(max - content.length <= 1){
                $(".charactersLeft").hide();
                $(".characterLeft").show();
            }else{
                $(".charactersLeft").show();
                $(".characterLeft").hide();
            }
        });
        editor.on('paste', function(e) {
            var content = tinymce.activeEditor.getContent({format : 'text'});  
            var bufferText = ((e.originalEvent || e).clipboardData || window.clipboardData).getData('Text');
            e.preventDefault();
            var all = content + bufferText;
            document.execCommand('insertText', false, all.trim().substring(0, max));
            if (typeof callbackMax == 'function') {
                callbackMax(max - content.length);
            }
            $(".character_remaning").show();
            $("#remaining-caracteres").text(max - content.length);
            console.log(max - content.length)
            if(max - content.length <= 0){
                $(".character_remaning").addClass("text-danger");
                console.log("zero or less")
            }else{
                $(".character_remaning").removeClass("text-danger");
            }
            if(max - content.length <= 1){
                $(".charactersLeft").hide();
                $(".characterLeft").show();
            }else{
                $(".charactersLeft").show();
                $(".characterLeft").hide();
            }
        });
        editor.on('blur', function(e) {
            var content = tinymce.activeEditor.getContent({format : 'text'});                 
            if (content.length <= 195) {
                $('#description').val(content);     
                $.ajax({
                    url: postEstablishmentPresentationUrl,
                    headers: {
                        'X-CSRFToken': token
                    },
                    type: 'post',
                    dataType: 'json',
                    data: {'presentation': content},
                    success: function (data) {
                        add_image_name_attribute();                      
                    },
                    error: function (xhr, status, error) {
                        handle_sticky_save('error');
                        console.log(error);
                    },
                });
            }
        });
    }
});
