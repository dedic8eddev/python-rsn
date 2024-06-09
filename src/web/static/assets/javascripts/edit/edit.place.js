var b_dropzone = null;
var b_dropzone_wl = null;

var image_manager = null;
var image_manager_wl = null;

var b_sortable = null;

var pdg_widget = null;

var b_dropzone_error_message = null;
var fileSelect = document.getElementById('id_image');
var statusDiv = document.getElementById('status');
statusDiv.style.display = 'none';




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
                //$("#container-current-winelists").html(data);
                image_manager_wl.refreshImages();
            },
            error: function(data){
                console.warn(data);
            }
        });

        $('#wl-refresh-button').trigger('click')
    }
}
$(document).on("click",".delete_winelist",function(){
    var wineId = $(this).data('wine-id');
    var wineName = $(this).data('wine-name');
    wl_delete(wineId,wineName)
})


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

$(document).on("click",".wl_details_open",function(){
    var wineId = $(this).data('wine-id');
    localStorage.setItem("winelist_file_id",$(this).data("winelistfile-id"));
    wl_details_open(wineId)
})

$("#modal-wl-details").on('hidden.bs.modal', function (e) {
    localStorage.removeItem("winelist_file_id");
});
function wl_details_update(id,parentIndex) {
    var serArray = $('select[name="incs"]').serializeArray();
    serArray.push({"name": "id", "value": id});
    serArray.push({"name": "moderated", "value": parentIndex});
    console.log(serArray);
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
$(document).on('change','select[name="incs"]',function(){
    var wineId = $(this).parents(".table").data('wine-id');
    var parentIndex = $(this).parents("tr").index();
    wl_details_update(wineId,parentIndex)
    var thiseSelect = $(this);

    var selectOption = thiseSelect.val();
    if(selectOption == 20){
        thiseSelect.attr("class","row-status form-control naturalSelected")
    }else if(selectOption == 30){
        thiseSelect.attr("class","row-status form-control bioOrganicSelected")
    }else if(selectOption == 25){
        thiseSelect.attr("class","row-status form-control notNaturalSelected")
    }else if(selectOption == 45){
        thiseSelect.attr("class","row-status form-control toInvestigateSelected")
    }else if(selectOption == 10){
        thiseSelect.attr("class","row-status form-control draftSelected")
    }else{
        thiseSelect.attr("class","row-status form-control")
    }
})
$(document).on("click",".btn_recalculate",function(){
    var wineId = $(this).data('wine-id');
    wl_details_update(wineId)
})


function wl_refresh_place_score(place_id) {
    $.ajax({
        type: "POST",
        dataType: "html",
        url: url_winelist_refresh_place_score_ajax,
        data: {
            "place_id": place_id
        },
        success: function(data) {
            console.log(data)
            image_manager_wl.refreshImages();
            alert("Total score for place has been recalculated");
        },
        error: function(data){
            console.warn(data);
        }
    });
}


$(document).on("click",".refresh_score",function(){
    var pid = $(this).data('place-id');
    wl_refresh_place_score(pid)
})

function wl_refresh_temp_place_score() {
    image_manager_wl.refreshImages();
    alert("Total score for place has been recalculated");
}

$(document).on("click",".refresh_temp_score",function(){
    // var pid = $(this).data('place-id');
    wl_refresh_temp_place_score()
})


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
        image_identifier_xhr_field:"id",

        callback: function(){
        }
//        current_images_request_data: {},
//        delete_image_request_data: {}
//        current_images_request_data: current_images_request_data_wm,
//        delete_image_request_data: delete_image_request_data_wm
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
    }
    // else if (street_addr != undefined && street_addr != null && street_addr != '' &&
    //     house_no != undefined && house_no != null && house_no != '') {
    //         var incStr = street_addr.includes(house_no);              
    //         if(incStr){
    //             $("#route").val(street_addr);
    //         }else{
    //             $("#route").val(house_no + " " + street_addr)
    //         }
    // }
    else if (street_addr != undefined && street_addr != null && street_addr != ''){
        $("#route").val(street_addr);
    }


//    $("#street_number").val($("#id_house_number").val());
    $("#postal_code").val($("#id_zip_code").val());
    $("#locality").val($("#id_city").val());
    $("#country").val($("#id_country").val());
    $("#administrative_area_level_1").val($("#id_state").val());

    $("#placeform").on('submit', function(){
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
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
});


// OCR


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


var csrf = $(".csrftoken").val();

function editOCR(id){
    $.ajax({
        url: '/ajax/ocr-recognize-task-result/?winelist_file_id=' + id,
        type: 'GET',
        success: function(response){
            console.log("preview shown")
            previewModal = '<div class="modal fade" id="previewModal" data-backdrop="static" data-keyboard="false" tabindex="-1" role="dialog">' +
                '<div class="modal-dialog" role="document">' +
                    '<div class="modal-content">' +
                        '<div class="modal-header">' +
                            '<h5 class="modal-title">Winelist preview</h5>' +
                            '<button type="button" class="close" data-dismiss="modal" aria-label="Close">' +
                                '<span aria-hidden="true">&times;</span>' +
                            '</button>' +
                        '</div>' +
                        '<div class="modal-body">' +
                            '<h4>Edit Wine list</h4>' +
                            '<p>Please note that once you remove elements from this wine list, they will be definitively deleted.</p>' +
                            '<textarea class="form-control winelist_data" rows="15">';                                                                 
                            $.each(response.ocred_text_rows, function (i, item) {  
                                previewModal +=  response.ocred_text_rows[i] + '\n'
                            }); 
            previewModal += '</textarea>' +
                        '</div>' +
                        '<div class="modal-footer">' +
                            '<button type="button" class="btn btn-success btn_analysis"  data-dismiss="modal">Start Analysis</button>' +
                            '<button type="button" class="btn btn-secondary" data-dismiss="modal">Cancel</button>' +
                        '</div>' +
                    '</div>' +
                ' </div>' +
            '</div>';
            $('body').append(previewModal)
            $('#previewModal').modal('show');
            $('#previewModal').on('hidden.bs.modal', function (e) {
                $(this).remove()
            })
        }
    }); 
}
    
$(document).on('click','.btn_analysis',function(){
    statusDiv.style.display = 'block'
    var calcStatus;
    var data   = {
        "text": $(this).parents('.modal').find(".winelist_data").val(),
        "winelist_file_id":  localStorage.getItem("winelist_file_id")
    }
    $.ajax({
        type: "POST",
        url: '/ajax/ocr-calc-task-create/',
        data: data,
        success: function(response){
            var ocr_calc_celery_task_id = response.ocr_calc_celery_task_id;
            var wineid = response.winelist_file_id;

            var requestCount = 0,
                delayCount = 1;
                countLimit = 10;
            newRequest();
            function newRequest(){
                requestCount++       
                $.ajax({
                    url: '/ajax/ocr-calc-task-status/?ocr_celery_task_id=' + ocr_calc_celery_task_id,
                    type: 'get',
                    success: function(response){
                        calcStatus = response.ocr_calc_celery_task_status;
                    },
                    complete: function() {
                        if(calcStatus === "SUCCESS"){                                        
                            $.ajax({
                                url: '/ajax/ocr-calc-task-result/?winelist_file_id=' + wineid,
                                type: 'get',
                                success: function(response){
                                    console.log("file uploaded")
                                    $('#previewModal').modal('hide').remove();
                                    $('.modal-backdrop').remove();
                                    $('body').removeClass('modal-open');
                                    statusDiv.style.display = 'none';
                                    fileSelect.value = '';
                                },
                                complete:function(){  
                                    var parentID; 
                                    if (place_id) {
                                       parentID = place_id;
                                    } else {
                                        parentID =  $("#id_images_temp_dir").val();
                                    }
                                    var dataPassed;
                                    if (window.location.href.indexOf("/place/add") > -1) {
                                        dataPassed   = {
                                            "winelist_file_id": localStorage.getItem("winelist_file_id"),
                                            "parent_id":  parentID,
                                            "is_temp": true
                                        }
                                    }else{
                                        dataPassed   = {
                                            "winelist_file_id": localStorage.getItem("winelist_file_id"),
                                            "parent_id":  parentID,
                                            "is_temp": false
                                        }
                                    }
                                    $.ajax({
                                        type: "POST",
                                        url: url_winelist_upload_ajax,
                                        data: dataPassed,
                                        success: function(response){
                                            image_manager_wl.refreshImages();
                                            $("#wl-refresh-button").show();
                                            $("#wl-refresh-button").trigger('click');
                                        }
                                    })
                                }
                            });    
                        }
                        else{
                            if (requestCount%5==0){
                                if(delayCount < countLimit){
                                    delayCount++
                                }
                                console.log("function called " + requestCount + " times  - " + 500 * delayCount  + " seconds")
                                setTimeout(function() { newRequest();}, 500 * delayCount);
                            }else{
                                setTimeout(function() { newRequest();}, 500 * delayCount);
                            }
                        }
                    }
                });
            }
        }
    });
})   

$(document).on("click",".edit_winelist",function(){    
    localStorage.setItem("winelist_file_id",$(this).data("winelistfile-id"));
    editOCR(localStorage.getItem("winelist_file_id"));
})

function getFileDetails(){

    event.preventDefault();


    // Get the files from the input
    var files = fileSelect.files;

    // Create a FormData object.
    var formData = new FormData();

    //Grab only one file since this script disallows multiple file uploads.
    var file = files[0]; 
    if(fileSelect.value != ''){
        
        statusDiv.style.display = 'block'
        // Add the file to the AJAX request.
        formData.append('image', file, file.name);


        
        // Set up the request.
        var xhr = new XMLHttpRequest();

        // Open the connection.
        xhr.open('POST', '/ajax/ocr-recognize-task-create/', true);

        function setHeaders(headers){
            for(let key in headers){
                xhr.setRequestHeader(key, headers[key]) 
            }
        }

        setHeaders({"csrfmiddlewaretoken":csrf,"X-CSRFToken": getCookie("csrftoken")})

        

        // Set up a handler for when the task for the request is complete.
        xhr.onload = function () {
            if (xhr.status === 200) {
                var previewModal;
               var celery_id = JSON.parse(this.responseText);
               localStorage.setItem("winelist_file_id", celery_id.winelist_file_id);
               var requestCount = 0,
                    delayCount = 1;
                    countLimit = 10;
                sendRequest();
                function sendRequest(){
                    requestCount++      
                    var status;
                    $.ajax({
                        url: '/ajax/ocr-recognize-task-status/?ocr_celery_task_id=' + celery_id.ocr_recognize_celery_task_id,
                        type: 'get',
                        success: function(response){
                               // console.log(response);
                                status = response.ocr_recognize_celery_task_status;
                        },
                        complete: function() {
                            if(status === "SUCCESS"){
                                statusDiv.style.display = 'none'
                                editOCR(celery_id.winelist_file_id);
                                
                            }
                            else{
                                if (requestCount%5==0){
                                    if(delayCount < countLimit){
                                        delayCount++
                                    }
                                    console.log("function called " + requestCount + " times  - " + 500 * delayCount  + " seconds")
                                    setTimeout(function() { sendRequest();}, 500 * delayCount);
                                }else{
                                    setTimeout(function() { sendRequest();}, 500 * delayCount);
                                }
                            }

                            
                        }
                    });
                };


               
            } else {
                statusDiv.innerHTML = 'Winelist file content is invalid. Try another file!';
            }
        };
        // Send the data.
        xhr.send(formData);
    }
    else{
            alert("Please select file to upload")
    }
}

function getpageLink(keyword){
    var arr = [];
    i = 0;
    $('.add_excluded_keyword').each(function(index, value) {
        var $this = $(this);;
        if(keyword.toLowerCase() === $this.data("keyword").toLowerCase()){
            arr[i++] = {"keyword": $this.data("keyword"),"link":$this.data("link")}   
            var keywordListArray = [...new Map(arr.map(item => [item["link"], item])).values()];
            console.log(keywordListArray)
            var keywordList = "";
            $.each(keywordListArray, function(i, item) {
                keywordList += '<a href="'+keywordListArray[i].link+'" target="_blank" class="selectedKeyword">'+keywordListArray[i].keyword+'</a><br>'; 
            }); 
           $('.keywordList').html(keywordList); 
        }
    });
    keywordListArray = [];
    arr = [];
}
var count=0;
$(document).on("click",".add_excluded_keyword",function(){
    var row_index = $(this).parents("tr").index();
    localStorage.setItem("row_index",row_index)
    count++
    if(count == 1){
        var $this = $(this);
        var selectedKeyword = $this.data("keyword");
        getpageLink(selectedKeyword);
        $("#addKeyword").modal('show');
        $(".btn_add_keyword").one("click",function(){
            var formData = new FormData();
            formData.append('word',  selectedKeyword);        
            var xhr = new XMLHttpRequest();
            xhr.open('POST', '/ajax/nwla/excluded-keywords/', true);
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken")) 
            xhr.onload = function () {
                if (xhr.status === 201) { 
                    var wineId = $this.parents(".table").data("wine-id");
                    statusDiv.style.display = 'block';
                    $.ajax({
                        type: "POST",
                        url: '/ajax/ocr-calc-task-create/',
                        data: { "winelist_file_id":  localStorage.getItem("winelist_file_id"),"new_exclusion_word_row":localStorage.getItem("row_index")},
                        success: function(response){
                            var ocr_calc_celery_task_id = response.ocr_calc_celery_task_id;
                            // var wineid = response.winelist_file_id;

                            var requestCount = 0,
                                delayCount = 1;
                                countLimit = 10;
                            newRequest();
                            function newRequest(){
                                requestCount++
                                $.ajax({
                                    url: '/ajax/ocr-calc-task-status/?ocr_celery_task_id=' + ocr_calc_celery_task_id,
                                    type: 'get',
                                    success: function(response){
                                        calcStatus = response.ocr_calc_celery_task_status;
                                    },
                                    complete: function() {
                                        if(calcStatus === "SUCCESS"){
                                            statusDiv.style.display = 'none';
                                            wl_details_open(wineId);
                                            $this.parents("span").remove();
                                            getExcludedKeyword();
                                        }
                                        else{
                                            if (requestCount%5==0){
                                                if(delayCount < countLimit){
                                                    delayCount++
                                                }
                                                console.log("function called " + requestCount + " times  - " + 500 * delayCount  + " seconds")
                                                setTimeout(function() { newRequest();}, 500 * delayCount);
                                            }else{
                                                setTimeout(function() { newRequest();}, 500 * delayCount);
                                            }
                                        }
                                    }
                                });

                            }
                        }
                    });
                }
                if (xhr.status === 400) {
                    alert("nwla excluded word with this word already exists.")
                }
            }      
            xhr.send(formData);
        })
        count=0;
    }
})

// addComment

function showCommentBox(){
    $('.comment_box').toggle();
    $('#id_team_comments').val("");
}


function getComment() {
    $.ajax({
        type: "GET",
        url: "/ajax/admincomments/place/" + place_id + "/",
        data:{"csrfmiddlewaretoken":getCookie("csrftoken")},
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
        // data:{"csrfmiddlewaretoken":getCookie("csrftoken")},
        beforeSend: function(xhr) {
            xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
        },
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
        url: "/ajax/admincomments/place/" + place_id + "/",
        data: {"content": comment,"csrfmiddlewaretoken":getCookie("csrftoken")},
        success: function(response) {
            
            $.ajax({
                type: "GET",
                url: "/ajax/admincomments/" + response.id + "/",
                data:{"csrfmiddlewaretoken":getCookie("csrftoken")},
                success: function(response) {
                    

                    
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
            // $('#commentList').find('tr').remove()
            // getComment();
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
