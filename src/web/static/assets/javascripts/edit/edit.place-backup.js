var b_dropzone = null;
var b_dropzone_wl = null;

var image_manager = null;
var image_manager_wl = null;

var b_sortable = null;

var pdg_widget = null;

var b_dropzone_error_message = null;


function loadRelatedLists(){
    loadAndInsertHtmlByAjax(ajax_related_lists_url, "related_lists");
}


function wl_delete(id, name) {
    if (confirm("Do you really want to delete this winelist (" + name + ")")) {
        $.ajax({
            type        : "POST",
            url         : url_winelist_delete_ajax,
            data        : {
                'id': id,
            },
            dataType    : 'html',
            success: function(data) {
                $("#container-current-winelists").html(data);
            },
            error: function(data){
                console.warn(data);
            }
        });
    }
}


function wl_details_open(id) {
    $.ajax({
        type        : "GET",
        url         : url_winelist_update_ajax,
        data        : {
            'id': id,
        },
        dataType    : 'html',
        success: function(data) {
            $("#modal-wl-details").html(data);
            $("#modal-wl-details").modal();
        },
        error: function(data){
            console.warn(data);
        }
    });
}


function wl_details_update(id) {
    var serArray = $('input[name^="incs"][type="checkbox"]:checked').serializeArray();
    serArray.push({"name": "id", "value": id});

    $.ajax({
        type: "POST",
        dataType: "html",
        url: url_winelist_update_ajax,
        data: serArray,
        success: function(data) {
            $("#modal-wl-details").html(data);
            image_manager_wl.refreshImages();
            alert("Results have been recalculated");
        },
        error: function(data){
            console.warn(data);
        }
    });
}

function wl_refresh_place_score(place_id) {
    $.ajax({
        type: "POST",
        dataType: "html",
        url: url_winelist_refresh_place_score_ajax,
        data: {
            "place_id": place_id
        },
        success: function(data) {
            comsole.log(data)
            image_manager_wl.refreshImages();
            alert("Total score for place has been recalculated");
        },
        error: function(data){
            console.warn(data);
        }
    });
}

function wl_refresh_temp_place_score(pid) {
    image_manager_wl.refreshImages();
    alert("Total score for place has been recalculated");
}


function confirm_save() {
    $("#modal_is_complete").modal("hide");
    $("#placeform").submit();
}

function cancel_save() {
    $("#modal_is_complete").modal("hide");
//    $("#placeform").submit();
}


init.push(function () {
    $("#btn-save").unbind('click');
    $("#btn-save").click(function(){
        var future_status = $("#id_status").val();
        // we don't have to display the message if we don't set "published"
        if (future_status != 20) {
            return true;
        }

        var name_str = $("#id_name").val();

        var is_bar       = $("#id_is_bar").prop('checked');
        var is_wine_shop = $("#id_is_wine_shop").prop('checked');
        var is_restaurant = $("#id_is_restaurant").prop('checked');
        var displayed_address = $("#route").val();
        var city = $("#locality").val();
        var country = $("#country").val();
        var state = $("#administrative_area_level_1").val();
        var zip_code = $("#postal_code").val();

        var uncover = [];

        if(name_str == undefined || name_str == null || name_str == '') {
            uncover.push('info-li-name');
        }

        if(displayed_address == undefined || displayed_address == null || displayed_address == '' ||
                city == undefined || city == null || city == '' ||
                country == undefined || country == null || country == '' ||
                state == undefined || state == null || state == '' ||
                zip_code == undefined || zip_code == null || zip_code == '') {
            uncover.push('info-li-address');
        }

        if(!is_bar && !is_wine_shop && !is_restaurant) {
            uncover.push('info-li-type');
        }

        $(".missing-fields-info ul li").hide();
        if(uncover.length > 0) {
            for(i in uncover ) {
                $("#"+uncover[i]).show();
            }
            $("#modal_is_complete").modal();
            return false;
        }
        return true;
    });
});

init.push(function () {
    if (!is_new) {
        loadRelatedLists();
    }
});


//init.push(function () {
//    if (!is_new) {
//        loadRelatedLists();
//    }
//});


// -------------------------------- datepicker on the right ----------------------------------

init.push(function () {
    b_sortable = new SortableManager("#current-images-inside", {
        'url_update_ordering_ajax': url_update_ordering_ajax,
        'parent_item_id': place_id
    });


    image_manager = new ImageManager($("#container-current-images"), {
        b_sortable: b_sortable,
        temp_image_ordering_field: is_new? 'id_image_ordering': null,
        url_current_images : url_current_images_ajax,
        url_delete_image : url_image_delete_ajax,
        image_identifier_xhr_field: is_new? "filename": "id",

        callback: function(){
            b_sortable.init();
        }
//        current_images_request_data: {},
//        delete_image_request_data: {}
//        current_images_request_data: current_images_request_data_wm,
//        delete_image_request_data: delete_image_request_data_wm
    });

    image_manager_wl = new ImageManager($("#container-current-winelists"), {
        b_sortable: null,
        temp_image_ordering_field: null,
        url_current_images : url_current_winelists_ajax,
        url_delete_image : url_winelist_delete_ajax,
        image_identifier_xhr_field: "id",

        callback: function(){
        }
//        current_images_request_data: {},
//        delete_image_request_data: {}
//        current_images_request_data: current_images_request_data_wm,
//        delete_image_request_data: delete_image_request_data_wm
    });
});

// summernote WYSIWYG editor
init.push(function () {
    if (! $('html').hasClass('ie8')) {
        $('#summernote-example').summernote({
            height: 200,
            tabsize: 2,
            codemirror: {
                theme: 'monokai'
            }
        });
    }
    $('#summernote-boxed').switcher({
        on_state_content: '<span class="fa fa-check" style="font-size:11px;"></span>',
        off_state_content: '<span class="fa fa-times" style="font-size:11px;"></span>'
    });
    $('#summernote-boxed').on($('html').hasClass('ie8') ? "propertychange" : "change", function () {
        var $panel = $(this).parents('.panel');
        if ($(this).is(':checked')) {
            $panel.find('.panel-body').addClass('no-padding');
            $panel.find('.panel-body > *').addClass('no-border');
        } else {
            $panel.find('.panel-body').removeClass('no-padding');
            $panel.find('.panel-body > *').removeClass('no-border');
        }
    });
});


// -----------------------------------------------------------------------------------------------
// business hours manager
var b_manager = null;

//var default_hours = [
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true},
//    {"timeFrom": "09:00:00", "timeTill": "20:00:00", "isActive": true}
//];

// business hours
init.push(function(){
    // don't forget to include required libs & styles
    // http://netdna.bootstrapcdn.com/bootstrap/3.0.3/js/bootstrap.min.js
    // http://netdna.bootstrapcdn.com/bootstrap/3.0.3/css/bootstrap.min.css"
    // http://netdna.bootstrapcdn.com/font-awesome/3.1.1/css/font-awesome.css
    // //cdnjs.cloudflare.com/ajax/libs/jquery-timepicker/1.2.17/jquery.timepicker.min.js
    // //cdnjs.cloudflare.com/ajax/libs/jquery-timepicker/1.2.17/jquery.timepicker.min.css


// turning off b_manager for now, not used in this version anymore, will be updated to PRO
//    b_manager = $("#businessHoursContainer1").businessHours({
//        operationTime: $("#id_opening_hours_week_json").val()!="" ? jQuery.parseJSON($("#id_opening_hours_week_json").val()) : default_hours,
//        postInit: function(){
//            $('.operationTimeFrom, .operationTimeTill').timepicker({
//                timeFormat: 'H:i',
//                step: 15
//            });
//        },
//        dayTmpl:'<div class="dayContainer" style="width: 80px;">' +
//            '<div data-original-title="" class="colorBox"><input class="invisible operationState" type="checkbox"></div>' +
//            '<div class="weekday"></div>' +
//            '<div class="operationDayTimeContainer">' +
//            '<div class="operationTime input-group"><span class="input-group-addon"><i class="fa fa-sun-o"></i></span><input name="startTime" class="mini-time form-control operationTimeFrom" value="" type="text"></div>' +
//            '<div class="operationTime input-group"><span class="input-group-addon"><i class="fa fa-moon-o"></i></span><input name="endTime" class="mini-time form-control operationTimeTill" value="" type="text"></div>' +
//            '</div></div>'
//    });
// /turning off b_manager for now, not used in this version anymore, will be updated to PRO

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


//    $("#street_number").val($("#id_house_number").val());
    $("#postal_code").val($("#id_zip_code").val());
    $("#locality").val($("#id_city").val());
    $("#country").val($("#id_country").val());
    $("#administrative_area_level_1").val($("#id_state").val());

    $("#placeform").on('submit', function(){
// turning off b_manager for now, not used in this version anymore, will be updated to PRO
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
//        $("#id_opening_hours_week_json").val(JSON.stringify(b_manager.serialize()));
// /turning off b_manager for now, not used in this version anymore, will be updated to PRO

        $("#id_full_street_address").val($("#route").val());

        $("#id_zip_code").val($("#postal_code").val());
        $("#id_city").val($("#locality").val());
        $("#id_country").val($("#country").val());
        $("#id_state").val($("#administrative_area_level_1").val());

        return true;
    });
});

// -----------------------------------------------------------------------------------------------
// dropzone.js file uploads

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


    b_dropzone = $("#dropzonejs-place").dropzone({
        url: url_image_upload_ajax,
        dictFileTooBig: "Error!\nPicture is bigger than {{maxFilesize}} K.O",

        sending: function(file, xhr, formData){

            $(".jq-growl-error-button-container").hide();
            // for edition (place exists)
            if (place_id) {
                formData.append('parent_id', place_id);
            // for creation (place does not exist)
            } else {
                formData.append('dir_name', $("#id_images_temp_dir").val());
            }
        },

        error: function(data, message) {
            $.growl.error({ "message": message });
//            $(".jq-growl-error-button-container").show();
//            $('#jq-growl-error').unbind('click');
//            $('#jq-growl-error').click(function () {
//                $.growl.error({ "message": message });
//                $(".jq-growl-error-button-container").hide();
//            });
        },

        complete: function(file){
            this.removeFile(file);
        },

        success: function(file, response){
//            image_manager.refreshImagesWithHtml(response);
            image_manager.refreshImages();
//            image_manager.handleImages();
        },

        paramName: "file", // The name that will be used to transfer the file
        maxFilesize: 2, // MB

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


init.push(function () {
    b_dropzone_wl = $("#dropzonejs-winelist-place").dropzone({
        url: url_winelist_upload_ajax,
        dictFileTooBig: "Error!\nWinelist file is bigger than {{maxFilesize}} K.O",

        sending: function(file, xhr, formData){
            $("#wl-refresh-button").hide();
            $("#spinner").show();
            $(".jq-growl-error-button-container").hide();
            // for edition (place exists)
            formData.append('to_bg', $("#id_to_bg").prop('checked'));
            if (place_id) {
                formData.append('parent_id', place_id);
            // for creation (place does not exist)
            } else {
                formData.append('parent_id', $("#id_images_temp_dir").val());
                formData.append('is_temp', true);
            }
        },

        error: function(data, message) {
            $.growl.error({ "message": message });
            $("#spinner").hide();
            $("#wl-refresh-button").show();

//            $(".jq-growl-error-button-container").show();
//            $('#jq-growl-error').unbind('click');
//            $('#jq-growl-error').click(function () {
//                $.growl.error({ "message": message });
//                $(".jq-growl-error-button-container").hide();
//            });
        },

        complete: function(file){
            this.removeFile(file);
            var no_files = Dropzone.forElement('#dropzonejs-winelist-place').getQueuedFiles().length;
            if (no_files < 1) {
                $("#spinner").hide();
                $("#wl-refresh-button").show();
                $("#wl-refresh-button").trigger('click');
                image_manager_wl.refreshImages();
            }
        },

        success: function(file, response){
//            image_manager.refreshImagesWithHtml(response);
            image_manager_wl.refreshImages();
//            image_manager.handleImages();
        },

//        totaluploadprogress: function(a,b,c) {
//            if (a==100 && b == 0 && c == 0) {
//                $("#spinner").hide();
//                $("#wl-refresh-button").show();
//            }
//        },



        paramName: "file", // The name that will be used to transfer the file
        maxFilesize: 30, // MB

        addRemoveLinks : true,
        dictResponseError: "Can't upload file!",
        dictDefaultMessage: "Upload files",
        //  When set to false you have to call myDropzone.processQueue() yourself in order to upload the dropped files. See below for more information on handling queues.
//        autoProcessQueue: false,
        thumbnailWidth: 138,
        thumbnailHeight: 120,

        previewTemplate: ['<div class="dropzone-uploading-container">',
                            '<img data-dz-thumbnail />',
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

init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
});
