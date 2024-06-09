var init = [];
var b_dropzone_wm = null;
var b_dropzone_wm_files = null;
var image_manager_wm = null;
var image_manager_wm_files = null;
var b_sortable_wm = null;

var pdg_widget = null;

var reloaded_for_rows  = [];


var wine_item_ordered_field_mapping = ['name', 'name_short', 'designation', 'grape_variety', 'color', 'year',
                                       'is_sparkling', 'wine_temp_dir', 'ordering'];


var TransEngine = {
    dd_tr_modified: {
    },

    json_decode_translations: function() {
        var dd_tr_source = $("#id_current_translations").val();
        if(dd_tr_source == undefined || dd_tr_source == null || dd_tr_source == '') {
            return null;
        }
        var dd_tr_json = JSON.parse(dd_tr_source);
        return dd_tr_json;
    },

    get_selected_language: function() {
        var sel_lang = $("#id_selected_language").val();
        return sel_lang;
    },

    get_current_contents: function() {
        var contents = $("#id_domain_description").val();
        return contents;
    },

    show_lang_version: function() {
        var lang_ver = TransEngine.get_selected_language();

        var dd_tr_json = TransEngine.json_decode_translations();
        if(dd_tr_json == undefined || dd_tr_json == null || dd_tr_json == '' ||
           dd_tr_json['translations'] == undefined ||
           dd_tr_json['translations'][lang_ver] == undefined) {
            return;
        }
        $("#id_domain_description").val(dd_tr_json['translations'][lang_ver]['text']);
        $("#id_trans_footer").html("Last modified version: " + dd_tr_json['translations'][lang_ver]['footer']);
    },

    clear_dd_translations: function() {
        if (!confirm("Are you sure you want to erase all data? All content will be lost.")) {
            return false;
        }

        $("#id_current_translations").val("");
        $("#id_domain_description").val("");
        $("#dd_tr_translate").show();
        $("#dd_tr_translations").hide();
        $.ajax({
            type: "POST",
            url: url_clear_dd,
            data: [
                {"name": "winemaker_id", "value": winemaker_id},
            ],
            success: function(data) {
                $("#id_current_translations").val(JSON.stringify(data['data']));
                $("#id_domain_description").val("");
            },
            error: function(data){
                console.warn(data);
            }
        });
    },

    update_dd_translations: function() {
        var lang_ver  = TransEngine.get_selected_language();
        var cur_cont  = TransEngine.get_current_contents();
        var str_trans = $("#id_current_translations").val();
        $.ajax({
            type: "POST",
    //            dataType: "html",
    //            contentType: "json",
            url: url_update_dd,
            data: [
                {"name": "winemaker_id", "value": winemaker_id},
                {"name": "contents", "value": cur_cont},
                {"name": "str_trans", "value": str_trans},
                {"name": "lang", "value": lang_ver}
            ],
            success: function(data) {
                if(data['status'] == 'OK') {
                    $("#id_current_translations").val(JSON.stringify(data['data']));
                    TransEngine.restore_dd_translations(false);
                }
            },
            error: function(data){
                console.warn(data);
            }
        });
    },

    restore_dd_translations: function(init_orig_lang) {
        var dd_tr_json = TransEngine.json_decode_translations();
        if(dd_tr_json == undefined || dd_tr_json == null || dd_tr_json == '') {
            return;
        }

        for(var i in dd_tr_json['translations']) {
            TransEngine.dd_tr_modified[i] = false;
        }

        if(init_orig_lang &&
            dd_tr_json['orig_lang'] != undefined &&
            dd_tr_json['orig_lang'] != null &&
            dd_tr_json['orig_lang'] != ''
        ) {
            $("#id_selected_language").val(dd_tr_json['orig_lang']);
        }

        $("#dd_tr_translate").hide();
        $("#dd_tr_translations").show();
        $("#id_selected_language").unbind('change');
        $("#id_selected_language").change(TransEngine.show_lang_version);
        $("#id_selected_language").trigger('change');
    },

    handle_translate_dd: function() {
        var orig_lang = $("#id_original_language").val();
        var contents = TransEngine.get_current_contents();
        if(orig_lang == undefined || orig_lang == null || orig_lang == '') {
            alert("Please select original language");
            return;
        }
        $("#tr-loading").modal();

        $.ajax({
            type: "POST",
    //            dataType: "html",
    //            contentType: "json",
            url: url_translate_dd,
            data: [
                {"name": "winemaker_id", "value": winemaker_id},
                {"name": "contents", "value": contents},
                {"name": "orig_lang", "value": orig_lang}
            ],
            success: function(data) {
                if(data['status'] == 'OK') {

                    var dd_tr_json = JSON.stringify(data['data']);
                    $("#id_current_translations").val(dd_tr_json);
                    TransEngine.restore_dd_translations(true);
                    $("#tr-loading").modal("hide");
                }
            },
            error: function(data){
                console.warn(data);
                $("#tr-loading").modal("hide");
                alert(data.responseJSON.data);
            }
        });
    }

};


function get_wine_item_field_index(field) {
    if (wine_item_ordered_field_mapping.indexOf(field) != -1) {
        return wine_item_ordered_field_mapping.indexOf(field);
    } else {
        return null;
    }
}


init.push(function () {
    Dropzone.prototype.accept = function(file, done) {
        if (file.size > this.options.maxFilesize * 1024 * 1024) {
            return done(this.options.dictFileTooBig.replace("{{filesize}}", Math.round(file.size / 1024 / 10.24) / 100).replace("{{maxFilesize}}", this.options.maxFilesize * 1000));
        } else if (!Dropzone.isValidFile(file, this.options.acceptedFiles)) {
            return done(this.options.dictInvalidFileType);
        } else if ((this.options.maxFiles != null) && this.getAcceptedFiles().length >= this.options.maxFiles) {
            done(this.options.dictMaxFilesExceeded.replace("{{maxFiles}}", this.options.maxFiles));
            return this.emit("maxfilesexceeded", file);
        } else {
            return this.options.accept.call(this, file, done);
        }
    };
});


function reload_wine_dropzones_image_managers(){
    $(".wine-row").each(function(){
        var attr_id = $(this).attr('id');
        //var id = attr_id.substr(9)
        val_row_number    = $(this).find("[name='wine_row_number[]']").val();
        var item_db_id    = $("#id_wines_" + val_row_number + "_" + get_wine_item_field_index('id')).val();
        var item_temp_dir = $("#id_wines_" + val_row_number + "_" + get_wine_item_field_index('wine_temp_dir')).val();

        if (reloaded_for_rows.indexOf(val_row_number) != -1) {
            return true;
        }

        reloaded_for_rows.push(val_row_number);

        if(item_db_id){
            var url_current_images_ajax_wine = url_current_images_ajax_wine_pattern.replace(/WINE_ID/, item_db_id);
            var url_image_delete_ajax_wine = url_image_delete_ajax_wine_pattern.replace(/WINE_ID/);
            var url_image_upload_ajax_wine = url_image_upload_ajax_wine_pattern; // no parameters

            var image_identifier_xhr = "id";

        }else if (item_temp_dir){
            var url_current_images_ajax_wine = url_current_images_ajax_wine_temp_pattern.replace(/TEMP_DIR/, item_temp_dir);
            var url_image_delete_ajax_wine = url_image_delete_ajax_wine_pattern.replace(/TEMP_DIR/, item_temp_dir);
            var url_image_upload_ajax_wine = url_image_upload_ajax_wine_temp_pattern; // no parameters
            var image_identifier_xhr = "filename";
        } else {
            return;
        }
        // -------------------------------------------------------------------------------------------------------
        // attach image manager

        var wine_row_id = "#container-current-wine-images-"+val_row_number;

        var b_sortable_wine = new SortableManager(wine_row_id+ " #current-images-inside", {
            'url_update_ordering_ajax': null,
            'parent_item_id': null,
            'ordering_field_id': "id_wines_"+val_row_number + "_" + get_wine_item_field_index('ordering')
        });

        var image_manager_wine = new ImageManager($(wine_row_id), {
            url_current_images : url_current_images_ajax_wine,
            'url_delete_image' : url_image_delete_ajax_wine,
            image_identifier_xhr_field: image_identifier_xhr,

            temp_image_ordering_field: "id_wines_" + val_row_number + "_" + get_wine_item_field_index('ordering'),
            b_sortable: b_sortable_wine,

            callback: function(){
                b_sortable_wine.init();
            }

    //        current_images_request_data: {},
    //        delete_image_request_data: {}
    //        current_images_request_data: current_images_request_data_wm,
    //        delete_image_request_data: delete_image_request_data_wm
        });
        // -------------------------------------------------------------------------------------------------------

        // attach dropzone
        b_dropzone_wine = $("#dropzonejs-wine-"+val_row_number).dropzone({
            url: url_image_upload_ajax_wine,
            dictFileTooBig: "Error!\nPicture is bigger than {{maxFilesize}} K.O",

            sending: function(file, xhr, formData){
    //            formData.append('photos_temp_dir', $("#form_photos_temp_dir").val());

                // for edition (wine exists)
                if (item_db_id) {
                    formData.append('parent_id', item_db_id);
                } else {
                    formData.append('dir_name', item_temp_dir);
                }
            },

            error: function(data, message) {
                console.log("MAX FILE SIZE", this.options.maxFilesize);
                console.log("ERROR", data);
                console.log("ERROR message", message);
                $.growl.error({ "message": message });
            },

            complete: function(file){
                this.removeFile(file);
            },

            success: function(file, response){
//                image_manager_wine.refreshImagesWithHtml(response);
                image_manager_wine.refreshImages();
                image_manager_wine.handleImages();
            },

            paramName: "file", // The name that will be used to transfer the file
            maxFilesize: 2,

            addRemoveLinks : true,
            dictResponseError: "Can't upload file!",
            dictDefaultMessage: "Upload files",
            //  When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. See below for more information on handling queues.
    //        autoProcessQueue: false,
            thumbnailWidth: 138,
            thumbnailHeight: 120,

            previewTemplate: [ '<div>',
                                '<img data-dz-thumbnail /><span class="dz-nopreview">No preview</span>',
                                '<span class="error text-danger" data-dz-errormessage>',
                                '<div class="progress progress-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">',
                                    '<div class="progress-bar progress-bar-success" style="width: 0%;" data-dz-uploadprogress></div>',
                                '</div>',
    
                            '</div>'].join(),

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
}

// dropzones and image managers for WINES
init.push(function () {
    reload_wine_dropzones_image_managers();
});

init.push(function () {
    var full_str_addr = $("#id_full_street_address").val();
    var street_addr = $("#id_street_address").val();
    var house_no = $("#id_house_number").val();

    if(full_str_addr != undefined && full_str_addr != null && full_str_addr != ''){
        $("#route").val(full_str_addr);
    }else if (street_addr != undefined && street_addr != null && street_addr != '' &&
        house_no != undefined && house_no != null && house_no != '') {
        $("#route").val(house_no + ", " + street_addr);
    }else if (street_addr != undefined && street_addr != null && street_addr != ''){
        $("#route").val(street_addr);
    }


    $("#postal_code").val($("#id_zip_code").val());
    $("#locality").val($("#id_city").val());
    $("#country").val($("#id_country").val());
    $("#administrative_area_level_1").val($("#id_state").val());
});






function handle_add_wine(){
    var max_row = 0;
    var initial_row = 0;

    $.each($("[name='wine_row_number[]']"), function (){
        var row_i  = parseInt($(this).val());
        max_row = Math.max(max_row, row_i);
    });

    if($("[name='wine_row_number[]']").length > 0){
        initial_row = max_row+1;
    }

    var url_add_wine= url_add_wine_pattern.replace(/INITIAL_ROW_NUMBER/, initial_row);

    $.ajax({
            type: "POST",
            dataType: "html",
            contentType: "html",
            url: url_add_wine,
            data: {},
            success: function(data) {
                $("#wines-list").append($(data));
                reload_wine_dropzones_image_managers();
            },
            error: function(data){
                console.warn(data);
            }
    });
}

function handle_delete_wine(){
    var max_row = 0;

    $.each($("[name='wine_row_number[]']"), function (){
        var row_i  = parseInt($(this).val());
        max_row = Math.max(max_row, row_i);
    });

    var wine_row_id = 'wine-row-' + max_row;
    var wine_id_field_name = 'wines_'+max_row+'_6';
    var $wine_obj = $("#"+wine_row_id);

    if(!$wine_obj.length){
        return false;
    }

    var wine_id = $("#"+wine_row_id).find("[type='hidden'][name='"+wine_id_field_name+"']").val();
    if(wine_id){
        x = confirm("The wine above is stored in the database - do you really want to remove it?");
        if(x){
            var serArray = [{
                "name" : "ids",
                "value" : wine_id
            }]

            $.ajax({
                    type: "POST",
                    url: url_delete_wine,
                    data: serArray,
                    success: function(data) {
                        $wine_obj.remove();
                    },
                    error: function(data){
                        console.warn(data);
                    }
            });

        }
    }else{
        $wine_obj.remove();
    }
}


init.push(function () {
    $("#btn_add").unbind("click");
    $("#btn_del").unbind("click");
    $("#btn_trans").unbind("click");
    $("#btn_trans_update").unbind("click");

    $("#btn_add").click(function(){
        handle_add_wine();
        return false;
    });

    $("#btn_del").click(function(){
        handle_delete_wine();
        return false;
    });

    $("#btn_trans").click(function() {
        TransEngine.handle_translate_dd();
        return false;
    })

    $("#id_domain_description").blur(function() {
        TransEngine.update_dd_translations();
    })

    TransEngine.restore_dd_translations(true);



});

init.push(function () {
    b_sortable_wm = new SortableManager("#current-images-inside", {
        'url_update_ordering_ajax': url_update_ordering_ajax,
        'parent_item_id': winemaker_id
    });

    image_manager_wm = new ImageManager($("#container-current-images-winemaker"), {
        temp_image_ordering_field: is_new? 'id_image_ordering': null,
        url_current_images : url_current_images_ajax_wm,
        url_delete_image : url_image_delete_ajax_wm,
        image_identifier_xhr_field: is_new? "filename": "id",

        b_sortable: b_sortable_wm,

        callback: function(){
            b_sortable_wm.init();
        }
        //        current_images_request_data: {},
        //        delete_image_request_data: {}
        //        current_images_request_data: current_images_request_data_wm,
        //        delete_image_request_data: delete_image_request_data_wm
    });

    image_manager_wm_files = new ImageManager($("#container-other-files"), {
        b_sortable: null,
        temp_image_ordering_field: null,
        url_current_images : url_current_wm_files_ajax,
        url_delete_image : url_wm_file_delete_ajax,
        image_identifier_xhr_field: is_new? "filename": "id",
        remove_btn_selector: 'a.remover',


        callback: function(){
            //            b_sortable.init();
        }
        //        current_images_request_data: {},
        //        delete_image_request_data: {}
        //        current_images_request_data: current_images_request_data_wm,
        //        delete_image_request_data: delete_image_request_data_wm
    });

});

// dropzone for WM (winemaker)
init.push(function () {
    b_dropzone_wm = $("#dropzonejs-winemaker").dropzone({
        url: url_image_upload_ajax_wm,

        error: function(data, message) {
            console.log("MAX FILE SIZE", this.options.maxFilesize);
            console.log("ERROR", data);
            console.log("ERROR message", message);
            $.growl.error({ "message": message });
        },

        sending: function(file, xhr, formData){
//            formData.append('photos_temp_dir', $("#form_photos_temp_dir").val());

            // for edition (winemaker exists)
            if (winemaker_id) {
                formData.append('parent_id', winemaker_id);
            } else {
                formData.append('dir_name', $("#id_images_temp_dir_wm").val());
            }
        },

        complete: function(file){
            this.removeFile(file);
        },

        success: function(file, response){
//            image_manager_wm.refreshImagesWithHtml(response);
            image_manager_wm.refreshImages(response);
            image_manager_wm.handleImages();
        },

        paramName: "file", // The name that will be used to transfer the file
        maxFilesize: 2, // MB

        dictFileTooBig: "Error!\nPicture is bigger than {{maxFilesize}} K.O",

        addRemoveLinks : true,
        dictResponseError: "Can't upload file!",
        dictDefaultMessage: "Upload files",
        //  When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. See below for more information on handling queues.
//        autoProcessQueue: false,
        thumbnailWidth: 138,
        thumbnailHeight: 120,

        previewTemplate: ['<div>',
            '<img data-dz-thumbnail /><span class="dz-nopreview">No preview</span>',
            '<span class="error text-danger" data-dz-errormessage>',
            '<div class="progress progress-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">',
                '<div class="progress-bar progress-bar-success" style="width: 0%;" data-dz-uploadprogress></div>',
            '</div>',

        '</div>'].join(),

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

init.push(function () {
    b_dropzone_wm_files = $("#dropzonejs-wm-files").dropzone({
        url: url_wm_file_upload_ajax,
        dictFileTooBig: "Error!\nFile file is bigger than {{maxFilesize}} K.O",

        sending: function(file, xhr, formData){
            $("#spinner").show();
            $(".jq-growl-error-button-container").hide();
            if (winemaker_id) { // for winemaker-edit (winemaker exists, permanent file)
                formData.append('parent_id', winemaker_id);
            } else {            // for winemaker-add (new winemaker, temp file)
                formData.append('dir_name', $("#id_images_temp_dir_wm").val());
            }
        },

        error: function(data, message) {
            console.log("MAX FILE SIZE", this.options.maxFilesize);
            console.log("ERROR", data);
            console.log("ERROR message", message);
            $.growl.error({ "message": message });
            $("#spinner").hide();
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
            //            if (_this.getUploadingFiles().length === 0 && _this.getQueuedFiles().length === 0) {
            //            }
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

        previewTemplate: ['<div>',
                '<img data-dz-thumbnail /><span class="dz-nopreview">No preview</span>',
                '<span class="error text-danger" data-dz-errormessage>',
                '<div class="progress progress-striped active" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0">',
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


init.push(function () {
    // Setup validation
    $("#jq-validation-form").validate({
        ignore: '.ignore, .select2-input',
        focusInvalid: false,
        rules: {
            'jq-validation-name': {
                required: true
            },

        },
        messages: {
            'jq-validation-policy': 'You must check it!'
        }
    });
});


// jq-datatables-wineposts --> edit.winemaker.list.wineposts.js


init.push(function () {
    $('#profile-tabs').tabdrop();

    $("#leave-comment-form").expandingInput({
        target: 'textarea',
        hidden_content: '> div',
        placeholder: 'Write message',
        onAfterExpand: function () {
            $('#leave-comment-form textarea').attr('rows', '3').autosize();
        }
    });

//    $("#jq-datatables-wineposts").attr("style", "");
});

init.push(function () {
    if(is_just_open) {
        handle_add_wine();
    }

    pdg_widget = new PDG_Widget({});
    pdg_widget.init();


});

// addComment

function showCommentBox(){
    $('.comment_box').toggle();
    $('#id_team_comments').val("");
}
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

function getComment() {
    $.ajax({
        type: "GET",
        url: "/ajax/admincomments/winemaker/" + winemaker_id + "/",
        data: {"csrfmiddlewaretoken":getCookie("csrftoken")},
        success: function(response) {
            if(response.length > 0){
                $('.commentList').show();
                $('.comment_info').removeClass("no_comments");
            }else{
                $('.comment_info').addClass("no_comments");
            }
            for (i = 0; i < response.length; i++) {
                var commentList = document.getElementById("commentList");
                if(current_user_id == response[i].author){
                    commentList.innerHTML += '<tr>' +
                                                '<td>' +
                                                    '<div class="commentMessage">'+ response[i].content +'</div>' +
                                                '</td>' +
                                                '<td class="commentAction">' +
                                                    '<a href="javascript:;" onclick="editComment('+  response[i].id  + ', `'  +    response[i].content +'`);" class="editComment  btn btn-xs btn-outline btn-success"><i class="fa fa-pencil"></i></a>' +
                                                    '<a href="javascript:;" onclick="confirmComment('+  response[i].id +');" class="deleteComment  btn btn-xs btn-outline btn-danger"><i class="fa fa-trash-o"></i></a>' +
                                                '</td>' +
                                            '</tr>' +
                                            '<tr>' +
                                                '<td colspan="2">' +
                                                    '<div class="comment_footer">' +
                                                        '<div class="commentBy"><a href="/user/edit/'+  response[i].author + '/">'+  response[i].author_name +'</a></div>' +
                                                        '<div class="commentDate">'+  response[i].created_formatted +'</div>' + 
                                                    '</div>' + 
                                                '</td>' +
                                            '</tr>';
                }else{
                    commentList.innerHTML += '<tr>' +
                                                '<td colspan="2>' +
                                                    '<div class="commentMessage">'+ response[i].content +'</div>' +
                                                '</td>' +
                                            '</tr>'+
                                            '<tr>' +
                                                '<td colspan="2">' +
                                                    '<div class="comment_footer">' +
                                                            '<div class="commentBy"><a href="/user/edit/'+  response[i].author + '/">'+  response[i].author_name +'</a></div>' +
                                                            '<div class="commentDate">'+  response[i].created_formatted +'</div>' + 
                                                    '</div>' + 
                                                '</td>' +
                                            '</tr>';
                }
            }
        },
        error: function(data){
            console.warn(data);
        }
    });
}

// delete comment

function deleteComment(commentId){
    $.ajax({
        type: "DELETE",
        url: "/ajax/admincomments/" + commentId + "/",
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
        // data: {"csrfmiddlewaretoken":getCookie("csrftoken")},
        success: function(response) {
            $('#commentList').find('tr').remove()
            getComment();

            if($('#commentList').find('tr').length == 0){
                $('.commentList').hide();
                $('.comment_info').addClass("no_comments");
            }else{
                $('.comment_info').removeClass("no_comments");
            }
        },
        error: function(data){
            console.warn(data);
        }
    });
}

// alter comment

function editComment(commentId,comment) {
    $('#id_team_comments').val(comment);
    $('.comment_box').show();
    $(".btn_updateComment").show();
    $('.btn_addComment').hide()
    var newComment = $('#id_team_comments').val();
    $('#id_team_comments').change(function(){
        newComment = $('#id_team_comments').val();
    })
    
    $('.btn_updateComment').click(function(){
        $(this).hide()
        $('#id_team_comments').val("");
        $('.comment_box').hide();
        $('.btn_addComment').show()
        $.ajax({
            type: "PUT",
            url: "/ajax/admincomments/" + commentId + "/",
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            data: {"content": newComment},
            success: function(response) {
                $('#commentList').find('tr').remove()
                getComment();
                commentId = null;
                
                console.clear();
            },
            error: function(data){
                console.warn(data);
            }
        });
    })
}


function addComment(){

    var comment = $('#id_team_comments').val()
    $.ajax({
        type: "POST",
        url: "/ajax/admincomments/winemaker/" + winemaker_id + "/",
        data: {"content": comment,"csrfmiddlewaretoken":getCookie("csrftoken")},
        success: function(response) {
            $.ajax({
                type: "GET",
                url: "/ajax/admincomments/" + response.id + "/",
                data: {"csrfmiddlewaretoken":getCookie("csrftoken")},
                success: function(response) {
                    console.log(response)
                    
                    if(current_user_id == response.author){
                        var NewComment = '<tr>' +
                                            '<td>' +
                                                '<div class="commentMessage">'+ response.content +'</div>' +    
                                            '</td>' +
                                            '<td class="commentAction">' +
                                                '<a href="javascript:;" onclick="editComment('+ response.id  + ', `'  +   response.content +'`);" class="editComment  btn btn-xs btn-outline btn-success"><i class="fa fa-pencil"></i></a>' +
                                                '<a href="javascript:;" onclick="confirmComment('+ response.id +');" class="deleteComment  btn btn-xs btn-outline btn-danger"><i class="fa fa-trash-o"></i></a>' +
                                            '</td>' +
                                        '</tr>' + 
                                        '<tr>' +
                                        '<td colspan="2">' +
                                            '<div class="comment_footer">' +
                                                '<div class="commentBy"><a href="/user/edit/'+ response.author + '/">'+ response.author_name +'</a></div>' +
                                                '<div class="commentDate">'+  response.created_formatted +'</div>' + 
                                            '</div>' +    
                                        '</td>' +
                                    '</tr>';
                    }else{
                        var NewComment = '<tr>' +
                                            '<td colspan="2>' +
                                                '<div class="commentMessage">'+ response.content +'</div>' +
                                            '</td>' +
                                        '</tr>' +
                                        '<tr>' +
                                            '<td colspan="2">' +
                                                '<div class="comment_footer">' +
                                                    '<div class="commentBy"><a href="/user/edit/'+ response.author + '/">'+ response.author_name +'</a></div>' +
                                                    '<div class="commentDate">'+  response.created_formatted +'</div>' + 
                                                '</div>' +
                                            '</td>' +
                                        '</tr>';
                    }

                    var tbody = $("#commentList");

                    if (tbody.children().length == 0) {
                        tbody.append(NewComment);
                        $('.commentList').show()
                    }else{
                        tbody.prepend(NewComment);
                    }
                    
                    $('.comment_info').removeClass("no_comments");
                    response.id = null
                },
                error: function(data){
                    console.warn(data);
                }
            });
            $('#id_team_comments').val("")
            $('.comment_box').hide()
            
        },
        error: function(data){
            console.warn(data);
        }
    });

}
function confirmComment(commentId){
    $('#confirmDelete').modal('show');
    $('.confirmDelete').off('click').on('click',function(){
        deleteComment(commentId);
    })
}
$(document).ready(function(){
    $('#commentList').find('tr').remove()
    getComment();
})

window.PixelAdmin.start(init);
