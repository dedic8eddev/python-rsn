
// $(document).ready(function ($) {

jQuery(function() {


    var fileSelect = document.getElementById('id_image');
    var statusDiv = document.getElementById('status');
    statusDiv.style.display = 'none';


    function dateFormat(inputDate) {
        const date = new Date(inputDate);

        var minutes = date.getMinutes() === 0 ? "00" : date.getMinutes();
    
        return date.getDate() + "-" +
        date.toLocaleDateString("en-US", { month: 'short' }) + "-" +
        date.getFullYear() + " " +
        date.getHours() + ":" +
        minutes;
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

    var csrf = $(".csrftoken").val();
    
    // get venue tab data

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
    

    function getImages(id) {
        $.ajax({
            type : "GET",
            url : "/ajax/ajax/images/place/current/" + id + "/",
            dataType : 'html',
            success: function(data) {
                $('.container-current-images-venue').html(data);
                //$( "#current-images-inside" ).sortable();

                    
                b_sortable = new SortableManager("#current-images-inside", {
                    'url_update_ordering_ajax': "/ajax/ajax/image/ordering/place/update/",
                    'parent_item_id': activeVenueId
                });


                image_manager = new ImageManager($("#container-current-images"), {
                            b_sortable: b_sortable,
                            temp_image_ordering_field: null,
                            url_current_images : null,
                            url_delete_image : null,
                            image_identifier_xhr_field: "id",

                            callback: function(){
                                b_sortable.init();
                            }
                });
            },
            error: function(data){
                console.warn(data);
            }
        });
    }


    function deleteImage(id){
        $.ajax({
            url: '/ajax/ajax/images/place/delete/',
            type: 'POST',
            data:{"id":id},
            dataType:"html",
            success: function(data) {
                if (confirm("Do you really want to delete this image? " + id)) {
                    $('.container-current-images-venue').html(data);

                    b_sortable = new SortableManager("#current-images-inside", {
                        'url_update_ordering_ajax': "/ajax/ajax/image/ordering/place/update/",
                        'parent_item_id': activeVenueId
                    });
    
    
                    image_manager = new ImageManager($("#container-current-images"), {
                                b_sortable: b_sortable,
                                temp_image_ordering_field: null,
                                url_current_images : null,
                                url_delete_image : null,
                                image_identifier_xhr_field: "id",
    
                                callback: function(){
                                    b_sortable.init();
                                }
                    });
                    //getImages(activeVenueId)
                }
            }
        });  
    }

    $(document).on('click', ".delete_image i", function(){
        var imgId = $(this).parents(".image-list-item").attr("cnt-data-image-file");
        deleteImage(imgId)
    })

    var venueId;
    var activeVenueId;

    var stickerDates = [];
    //var newStickerList = [];
    stickerDates =  JSON.parse(localStorage.getItem("stickerDates"));


    function getVenueData(venueId){
        $.ajax({
            url: '/right-panel/place/edit/' + venueId + '/',
            type: 'get',
            success: function(response){
                $("#sidebarStatus").hide()
                $(".venueName").text(response.name);
                $("#venueName").val(response.name);
                $("#venuePhone").val(response.phone_number);
                $("#is_restaurant").prop("checked", response.is_restaurant);
                $("#is_bar").prop("checked", response.is_bar);
                $("#is_wine_shop").prop("checked", response.is_wine_shop);
                $("#venueType option[value='" + response.status + "']").prop('selected', true);
                $("#venueEmail").val(response.email);
                $("#venueWebsite").val(response.website_url);
                $("#venueFBUrl").val(response.social_facebook_url);
                $("#venueInstaUrl").val(response.social_instagram_url);
                $("#venueTwitterUrl").val(response.social_twitter_url);
                $("#missing option[value='" + response.missing_info + "']").prop('selected', true);
                if(response.type_sub){
                    $("#type-sub option[value='" + response.type_sub + "']").prop('selected', true);
                }else{
                    $("#type-sub option[value='']").prop('selected', true);
                }                
                $("#url-post").val(response.media_post_url);
                $("#media-post-date").val(response.media_post_date);

                var dateList = document.getElementById("stickerDate");
                dateList.innerHTML = "";

                if (response.name) {
                    var option_place = new Option(response.name, venueId, true);
                    $("#id_place").append(option_place).trigger('change');
                    $("#nameOfVenue").text(response.name);
                }

                if (response.id && !$("#id_customer").val()) {
                    $("#id_customer").val(response.id);
                }

                if(response.sticker_sent_dates == null){
                    $("#stickerDate").text("");
                    $("#sticker_sent_date").val("");
                    localStorage.removeItem("stickerDates");
                    stickerDates = null;
                }else{
                    localStorage.setItem("stickerDates",JSON.stringify(response.sticker_sent_dates));    
                    stickerDates =   JSON.parse(localStorage.getItem("stickerDates"));
                }

                if (response.src_info && response.src_info === 10) {
                    $("#origin option[value='PRO_WEBSITE']").prop('selected', true);
                    $("#originNoOwner option[value='PRO_WEBSITE']").prop('selected', true);
                }
                if (response.src_info && response.src_info === 20) {
                    $("#origin option[value='MOBILE_APP']").prop('selected', true);
                    $("#originNoOwner option[value='MOBILE_APP']").prop('selected', true);
                }
                if (response.src_info && response.src_info === 30) {
                    $("#origin option[value='CHARGEBEE']").prop('selected', true);
                    $("#originNoOwner option[value='CHARGEBEE']").prop('selected', true);
                        
                }
                if (response.src_info && response.src_info === 40) {
                    $("#origin option[value='CMS']").prop('selected', true);
                    $("#originNoOwner option[value='CMS']").prop('selected', true);
                }


                if (response.src_info && response.src_info === 30 && localStorage.getItem("ownerAvailability") == "notAvailable"){
                    $(".noOwnerVenue").show();
                    $(".venue_fields").hide();
                } else{
                    $(".noOwnerVenue").hide();
                    $(".venue_fields").show();
                }   


                var options1 = {                                   
                    // autoclose: true,
                    format: "yyyy-mm-dd",
                    container: '#owner',
                    multidate: true,
                }
                var dateList = document.getElementById("stickerDate");

                $('#sticker_sent_date').datepicker(options1).on('changeDate', function(e) {
                    var stickerDate = $(this).val();
                        dateList.innerHTML = "";
                        stickerDates =  stickerDate.split(',');

                    localStorage.setItem("stickerDates", JSON.stringify(stickerDates));
                    stickerDates =   JSON.parse(localStorage.getItem("stickerDates"));

                    if(stickerDates.length > 0){
                        for(var i =0; i < stickerDates.length; i++){
                            dateList.innerHTML += '<li class="checkbox"><input type="checkbox" value="'+stickerDates[i]+'" checked id="check' + [i] + '"><label for="check' + [i]+ '"> <b>' + stickerDates[i].substring(0,4) + '</b> - ' + stickerDates[i] + ' <a title="Delete vintage" class="year-delete-btn"><i class=" fa fa-times-circle"></i></a></label></li>'
                        } 
                    }
                });
                $(document).on('change', '#stickerDate input[type="checkbox"]', function() {
                    var id = $(this).val(); 
                    var index;
                    var $this = $(this);
                    if(stickerDates.length > 0){
                        stickerDates = JSON.parse(localStorage.getItem("stickerDates"));
                        index = stickerDates.indexOf(id);
                    }
                    if(!$(this).is(':checked')){
                        if (index > -1) {
                            stickerDates.splice(index, 1);
                            localStorage.setItem("stickerDates", JSON.stringify(stickerDates))  
                            stickerDates =   JSON.parse(localStorage.getItem("stickerDates"));
                            $this.parent("li").remove()
                            if(stickerDates.length == 0){
                                localStorage.removeItem("stickerDates") 
                                stickerDates = null;
                            }
                            $("#sticker_sent_date").datepicker("setDate",stickerDates);
                        }
                    }   
                })

                if(localStorage.getItem("stickerDates")){
                    stickerDates =   JSON.parse(localStorage.getItem("stickerDates"));
                    $("#sticker_sent_date" ).datepicker("setDate",stickerDates);
                }else{
                        stickerDates = null
                }

                if (response.media_post_date == null){
                    localStorage.removeItem("mediaPost");
                }else{
                    localStorage.setItem("mediaPost",response.media_post_date);
                }

        
                if( response.comments_by_team.length > 0){
                    $('.commentList').show();
                    $('.comment_info').removeClass("no_comments");
                }else{
                    $('.comment_info').addClass("no_comments");
                }
                var commentList = document.getElementById("commentList");
                commentList.innerHTML = "";
                for (i = 0; i < response.comments_by_team.length; i++) {
                        commentList.innerHTML += '<tr>' +
                                                    '<td>' +
                                                        '<div class="commentMessage">'+ response.comments_by_team[i].content +'</div>' +
                                                    '</td>' +
                                                    '<td class="commentAction">' +
                                                        '<a href="javascript:;" data-comment-id="'+response.comments_by_team[i].id +'" data-comment-content="'+ response.comments_by_team[i].content+'" class="editComment btn btn-xs btn-outline btn-success"><i class="fa fa-pencil"></i></a>' +
                                                        '<a href="javascript:;" data-comment-id="'+ response.comments_by_team[i].id+'" class="deleteComment  btn btn-xs btn-outline btn-danger"><i class="fa fa-trash-o"></i></a>' +
                                                    '</td>' +
                                                '</tr>' +
                                                '<tr>' +
                                                    '<td colspan="2">' +
                                                        '<div class="comment_footer">' +
                                                            '<div class="commentBy"><a href="/user/edit/'+  response.comments_by_team[i].author + '/">'+  response.comments_by_team[i].author_name +'</a></div>' +
                                                            '<div class="commentDate">'+  response.comments_by_team[i].created_formatted +'</div>' + 
                                                        '</div>' + 
                                                    '</td>' +
                                                '</tr>';
                    
                }
                // map fields

                if(response.full_street_address) {
                    var route = response.full_street_address;
                }else {
                    var route = "";
                }
    
                if(response.city) {
                    var city = response.city;
                } else {
                    var city = "";
                }
    
                if(response.state) {
                    var state = response.state;
                } else {
                    var state  = "";
                }
    
                if(response.zip_code) {
                    var zip_code = response.zip_code;
                } else {
                    var zip_code  = "";
                }
    
                if(response.country) {
                    var country = response.country;
                } else {
                    var country  = "";
                }
                if(response.house_number) {
                    var house_number = response.house_number;
                } else {
                    var house_number  = "";
                }
                if(response.country_iso_code) {
                    var country_iso_code = response.country_iso_code;
                } else {
                    var country_iso_code  = "";
                }

                if(response.latitude) {
                    var latitude = response.latitude;
                } else {
                    var latitude  = "48.8588376";
                }

                if(response.longitude) {
                    var longitude = response.longitude;
                } else {
                    var longitude  = "2.2773452";
                }

                if (!response.longitude && !response.latitude) {
                    $('#addressLine').addClass("error_autocomplete");
                    $('#route').addClass("error_autocomplete");

                    if (response.country === "Japan") {
                        $('#autocomplete-jp').addClass("error_autocomplete");
                    } else {
                        $('#autocomplete').addClass("error_autocomplete");
                    }
                }else{

                    $('#addressLine').removeClass("error_autocomplete");
                    $('#route').removeClass("error_autocomplete");
                    $('#autocomplete').removeClass("error_autocomplete");
                    $('#autocomplete-jp').removeClass("error_autocomplete");
                    
                }

                if(response.pin_latitude) {
                    var pin_latitude = response.pin_latitude;
                } else {
                    var pin_latitude  = "48.8588376";
                }

                if(response.pin_longitude) {
                    var pin_longitude = response.pin_longitude;
                } else {
                    var pin_longitude  = "2.2773452";
                }
                

                if(route || city || zip_code || state || country){
                    $("#addressLine").html('<i class="fa fa-compass" style="font-size:20px;"></i><span>'+route+'</span>' + '<span>'+city+'</span>' + '<span>'+zip_code+'</span>' + '<span>'+state+'</span>' +  '<span>'+country+'</span>')
                }else{
                    $("#addressLine").html('<i class="fa fa-compass" style="font-size:20px;"></i> Venue Address')
                }

                if (route){
                    $("#route").val(route);
                    $("#id_street_address").val(route);
                    $("#id_full_street_address").val(route);
                }
                else{
                    $("#route").val("");
                    $("#id_street_address").val("");
                    $("#id_full_street_address").val("");
                }


                $("#id_house_number").val(house_number);

                $("#postal_code").val(zip_code);
                $("#id_zip_code").val(zip_code);

                $("#locality").val(city);
                $("#id_city").val(city);

                $("#country").val(country);
                $("#id_country").val(country);

                $("#id_country_iso_code").val(country_iso_code);

                $("#administrative_area_level_1").val(state);
                $("#id_state").val(state);


                $("#id_latitude").val(latitude);
                $("#id_longitude").val(longitude);
            
                $("#id_pin_latitude").val(pin_latitude);
                $("#id_pin_longitude").val(pin_longitude);

                initMap();

                latitude = parseFloat(latitude);
                longitude = parseFloat(longitude);
                // initMap2(latitude,longitude);


                // var totalImages = "";
                // $("#totalPictures").val(totalImages);               
                var options = {                                   
                    autoclose: true,
                    format: "yyyy-mm-dd",
                    container: '#owner'
                }
            
        
                $('#media-post-date').datepicker(options).on('changeDate', function(e) {
                    localStorage.setItem("mediaPost",$(this).val());
                    if ($(this).val() == ''){
                        localStorage.removeItem("mediaPost");
                    }else{
                        localStorage.setItem("mediaPost",$(this).val());
                    }
                });
                hideShowResetButton();
            }
        });

    }

    function hideShowResetButton(){
        $('#Venue-content input').map(function(){
            if($(this).val() === ""){
                $(this).prev().hide();
            }
        });
        $('#owners-content input').map(function(){
            if($(this).val() === ""){
                $(this).prev().hide();
            }
        });
    }

    function updateVenueData(venueId){
        var sticker_sent_dates = JSON.parse(localStorage.getItem("stickerDates"));
        var url = '/right-panel/place/edit/' + venueId + '/';
        formData = new FormData(),
        xhr = new XMLHttpRequest();

        formData.append("name", $("#venueName").val());
        formData.append("phone_number", $("#venuePhone").val());
        formData.append("is_bar",$("#is_bar").is(':checked') ? true : false);
        formData.append("is_wine_shop", $("#is_wine_shop").is(':checked') ? true : false);
        formData.append("is_restaurant",$("#is_restaurant").is(':checked') ? true : false);
        formData.append("phone_number", $("#venuePhone").val());
        formData.append("status",  $("#venueType option:selected").val());
        formData.append("email", $("#venueEmail").val());
        formData.append("website_url", $("#venueWebsite").val());
        formData.append("social_facebook_url",$("#venueFBUrl").val());
        formData.append("social_instagram_url", $("#venueInstaUrl").val());
        formData.append("social_twitter_url", $("#venueTwitterUrl").val());

        if($("#id_full_street_address").val()){
            formData.append("full_street_address", $("#id_full_street_address").val());
            formData.append("street_address", $("#id_full_street_address").val());
        }else{
            formData.append("full_street_address", $("#id_street_address").val());
            formData.append("street_address", $("#id_street_address").val());
        }



        
        formData.append("house_number", $("#id_house_number").val());
        formData.append("zip_code", $("#postal_code").val());
        formData.append("city", $("#locality").val());
        formData.append("country", $("#country").val());
        formData.append("state", $("#administrative_area_level_1").val());
        formData.append("country_iso_code", $("#id_country_iso_code").val());
        formData.append("latitude", $("#id_latitude").val());
        formData.append("longitude", $("#id_longitude").val());
        formData.append("pin_latitude", $("#id_pin_latitude").val());
        formData.append("pin_longitude", $("#id_pin_longitude").val());
        formData.append("missing_info", $("#missing option:selected").val());
        formData.append("type_sub", $("#type-sub option:selected").val());
        formData.append("media_post_url", $("#url-post").val());
        if ($("#origin option:selected").val() === 'PRO_WEBSITE') {
            formData.append("src_info", 10);
        }
        if ($("#origin option:selected").val() === 'MOBILE_APP') {
            formData.append("src_info", 20);
        }
        if ($("#origin option:selected").val() === 'CHARGEBEE') {
            formData.append("src_info", 30);
        }
        if ($("#origin option:selected").val() === 'CMS') {
            formData.append("src_info", 40);
        }
        

        if(localStorage.getItem("mediaPost")){
            formData.append("media_post_date", localStorage.getItem("mediaPost"));
        }
        if(localStorage.getItem("stickerDates")){
            if(sticker_sent_dates.length > 0){
                for(var i = 0; i < sticker_sent_dates.length; i++){
                    formData.append("sticker_sent_dates",sticker_sent_dates[i]);
                } 
            }
        }
        xhr.open('PATCH', url, true);

        // xhr.responseType = 'json';
        function setHeaders(headers){
            for(let key in headers){
                xhr.setRequestHeader(key, headers[key]) 
            }
        }
        setHeaders({"X-CSRFToken":getCookie("csrftoken")})
        xhr.onload = function () {
            if (xhr.status === 200) {
                //$("#sidebarStatus").hide()  
                
                if($("#id_full_street_address").val()){
                    $("#addressLine").html('<i class="fa fa-compass" style="font-size:20px;"></i><span>'+$("#id_full_street_address").val()+'</span>' + '<span>'+$("#locality").val()+'</span>' + '<span>'+$("#postal_code").val()+'</span>' + '<span>'+$("#administrative_area_level_1").val()+'</span>' +  '<span>'+$("#country").val()+'</span>');
                }else{
                    $("#addressLine").html('<i class="fa fa-compass" style="font-size:20px;"></i><span>'+$("#id_street_address").val()+'</span>' + '<span>'+$("#locality").val()+'</span>' + '<span>'+$("#postal_code").val()+'</span>' + '<span>'+$("#administrative_area_level_1").val()+'</span>' +  '<span>'+$("#country").val()+'</span>');
                }


                if(localStorage.getItem("ownerAvailability") == "Available"){
                    updateOwnerData(venueId);  
                }else{
                    addUser(venueId)
                }

                b_datatable_in_trial.ajax.reload();
                b_datatable_subscribers.ajax.reload();
                b_datatable_all.ajax.reload();
                b_datatable_free.ajax.reload();
                b_datatable_not_connected.ajax.reload();
                b_datatable_stickers.ajax.reload();

                // for (key in formData) {
                //     if (formData.hasOwnProperty(key)) {
                //         console.log(key + " = " + formData[key]);                        
                //     }
                // }
            }else{
                console.log(`Error ${xhr.status}: ${xhr.statusText}`)
            }
        };
        xhr.send(formData); 
    }



    // upload venue image

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
            url: "/ajax/image/upload/place/",
            dictFileTooBig: "Error!\nPicture is bigger than {{maxFilesize}} K.O",
    
            sending: function(file, xhr, formData){
    
                $(".jq-growl-error-button-container").hide();
                // for edition (place exists)
                if (activeVenueId) {
                    formData.append('parent_id', activeVenueId);
                // for creation (place does not exist)
                } else {
                    formData.append('dir_name', $("#id_images_temp_dir").val());
                }
            },
    
            error: function(data, message) {
                $.growl.error({ "message": message });
            },
    
            complete: function(file){
                this.removeFile(file);
            },
    
            success: function(file, response){
                getImages(activeVenueId)
            },
    
            paramName: "file", // The name that will be used to transfer the file
            maxFilesize: 2, // MB
    
            addRemoveLinks : true,
            dictResponseError: "Can't upload file!",
            dictDefaultMessage: "Upload files",
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
    
    // OCR


    function getWineScore(){
        $.ajax({
            type        : "GET",
            url         : "/ajax/ajax/right-panel/winelist/items/list/" + activeVenueId + "/",
            success: function(response) {  
                $("#wineScore").text(response.scores.total_wl_score + "%");
                $("#wineUpdateDate").text(response.scores.last_wl_an_time ? response.scores.last_wl_an_time : "");
            }, 
            error: function(data){
                console.warn(data);
            }
        });
    }

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
        statusDiv.style.display = 'block';
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
                                        statusDiv.style.display = 'none';
                                        fileSelect.value = '';
                                    },
                                    complete:function(){    
                                        
                                        var parentID; 
                                        if (activeVenueId) {
                                            parentID = activeVenueId;
                                        } else {
                                            parentID =  $("#id_images_temp_dir").val();
                                        }
                                        var dataPassed   = {
                                                "csrfmiddlewaretoken":csrf,
                                                "winelist_file_id":  localStorage.getItem("winelist_file_id"),
                                                "parent_id":  parentID,
                                                "is_temp": false
                                        }

                                        $.ajax({
                                            type: "POST",
                                            url: "/ajax/ajax/winelist/item/upload/",
                                            data: dataPassed,
                                            success: function(response){
                                                // image_manager_wl.refreshImages();
                                                // $("#wl-refresh-button").show();
                                                // $("#wl-refresh-button").trigger('click');

                                                getWineData();
                                                getWineScore();
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
        localStorage.setItem("winelist_file_id",$(this).data("winelistfile-id"))
        editOCR(localStorage.getItem("winelist_file_id"))
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

    function getWineData(){
        $.ajax({
            type        : "GET",
            url         : "/ajax/ajax/winelist/items/list/" + activeVenueId,
            // data        : {"csrfmiddlewaretoken":getCookie("csrftoken")},
            dataType    : "html",

            success: function(data) {
                $("#container-current-winelists").html(data);   
            },
            error: function(data){
                console.warn(data);
            }
        });
    }

    function wl_delete(id, name) {
        if (confirm("Do you really want to delete this winelist (" + name + ")")) {
            $.ajax({
                type        : "POST",
                url         : "/ajax/ajax/winelist/item/delete/",
                data        : {
                    'id': id,
                },
                dataType    : 'html',
                success: function(data) {
                    getWineData();
                    getWineScore();
                    $('#wl-refresh-button').trigger('click')
                },
                error: function(data){
                    console.warn(data);
                }
            });
        }
    }

    $(document).on("click",".delete_winelist",function() {
        var wineId = $(this).data('wine-id');
        var wineName = $(this).data('wine-name');
        wl_delete(wineId,wineName)
        wl_refresh_place_score(activeVenueId)
    })
    
    
    function wl_details_open(id) {
        $.ajax({
            type        : "GET",
            url         : "/ajax/ajax/winelist/item/update/",
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
            url: "/ajax/ajax/winelist/item/update/",
            data: serArray,
            success: function(data) {
                $("#modal-wl-details").html(data);
                getWineData();
                getWineScore();
                alert("Results have been recalculated");
            },
            error: function(data){
                console.warn(data);
            }
        });
    }

    $(document).on("click",".btn_recalculate",function(){
        var wineId = $(this).data('wine-id');
        wl_details_update(wineId)
    })


    function wl_refresh_place_score(place_id) {
        $.ajax({
            type: "POST",
            dataType: "html",
            url: "/ajax/ajax/winelist/refresh_place_score/" + place_id + "/",
            success: function(data) {
                getWineData();
                getWineScore();
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
        getWineData();
        getWineScore();
        alert("Total score for place has been recalculated");
    }
    
    $(document).on("click",".refresh_temp_score",function(){
        wl_refresh_temp_place_score()
    })

    $(".btn_process_file").on("click",function(){
        getFileDetails();
    })
    


    //addComment

    $(".addComment").on("click",function(){
        $('.comment_box').toggle();
        $('#id_team_comments').val("");
    })

    //delete comment

    
    $(document).on("click",".deleteComment",function(){
        var commentId = $(this).data('comment-id');
        $('#confirmDelete').modal('show');
        $('.confirmDelete').off('click').on('click',function(){
            $(".sidebar_quickview").addClass("reveal")
            deleteComment(commentId);
        })        
    });


    function deleteComment(commentId){
        $.ajax({
            type: "DELETE",
            url: "/ajax/admincomments/" + commentId + "/",
            beforeSend: function(xhr) {
                xhr.setRequestHeader("X-CSRFToken", getCookie("csrftoken"));
            },
            success: function(response) {
                $('#commentList').find('tr').remove();
                
                getVenueData(activeVenueId)
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
        
        $('.btn_updateComment').on("click",function(){
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

                getVenueData(activeVenueId)
                commentId = null;
                    
                },
                error: function(data){
                    console.warn(data);
                }
            });
        })
    }

    $(document).on('click','.editComment',function(){
        var commentId = $(this).data('comment-id');
        var comment = $(this).data('comment-content');
        editComment(commentId,comment)
    })

    $('.btn_addComment').on("click",function(){
        var comment = $('#id_team_comments').val()
        $.ajax({
            type: "POST",
            url: "/ajax/admincomments/place/" + activeVenueId + "/",
            data: {"content": comment,"csrfmiddlewaretoken":getCookie("csrftoken")},
            success: function(response) {
                $('#commentList').find('tr').remove()
                getVenueData(activeVenueId)
                $('#id_team_comments').val("")
                $('.comment_box').hide()
            },
            error: function(data){
                console.warn(data);
            }
        });
    })



    

    // get owner tab data

    var all_subscriptions_by_ids = {};
    function load_subscriptions(customer_id){
        select_subscription = $('#id_subscription').select2({
            allowClear: true,
            width: '100%',
            dropdownParent: $('#subscription_id'),
            placeholder: 'Select Subscription for Place...',
            ajax: {
                url: "/ajax/autocomplete/place/subscriptions/list",
                dataType: 'json',
                delay: 250,
                data: { 'customer': customer_id },
                processResults: function (data) {
                    for (var i in data.items){
                        var item0 = data.items[i];
                        all_subscriptions_by_ids[item0.id] = item0;
                    }
                    return {
                        results: $.map(data.items, function(item){
                            return {
                                text: item.list_format,
                                id: item.id,
                            };
                        }),
                    };
                },
                cache: true,
                error: function(data){
                    console.log(data);
                }
            }
        });
    }


    function getOwnerData(venueId){
        $(".invalidEmail").hide();
        $(".invalidExtraEmail").hide();
        $(".invalidLanguage").hide();
        $(".requiredUsername").hide();
        $(".requiredEmail").hide();
        $(".requiredCustomerID").hide();
        $(".requiredSubscription").hide();
        $('.subscrptionalreadyUsed').hide();
        $(".requiredVenue").hide();
        $("#id_subscription").text("");
        $("#id_place").text("");

        $.ajax({
            url: '/right-panel/place/owner/edit/' + venueId,
            type: 'get',
            success: function(response){
                $("#ownerEmail").val(response.email);
                $("#ownerName").val(response.full_name);
                $("#ownerUsername").val(response.username);
                $("#ownerExtraEmail").val(response.secondary_emails);
                $("#ownerWebsite").val(response.website_url);
                $("#origin option[value='" + response.origin + "']").prop('selected', true);
                $("#ownerStatus option[value='" + response.type + "']").prop('selected', true);
                $("#id_customer").val(response.customer_id);

                if (response.lang) {
                    $("#ownerlanguage option[value='" + response.lang + "']").prop('selected', true);
                } else {
                    $("#ownerlanguage option[value='FR']").prop('selected', true);
                }
                // localStorage.setItem("id_customer",response.customer_id);
                load_subscriptions(response.customer_id);
                response.username ?
                localStorage.setItem("username",response.username) :
                localStorage.removeItem("username");


                var option = new Option(response.subscription, response.subscription, true);
                $("#id_subscription").append(option).trigger('change');
            
                $("#id_subscription").trigger({
                    type: 'select2:select',
                    params: {
                        data: response.subscription
                    }
                });
    
                var option1 = new Option(response.name, venueId, true);
                $("#id_place").append(option1).trigger('change');
                $("#id_place").trigger({
                    type: 'select2:select',
                    params: {
                        data: response
                    }
                });

                
                $("#proDashLink").attr("href",'/pro/dashboard/' + venueId);
                $("#userProfile").attr("src", response.profile_photo);

                localStorage.setItem("ownerAvailability","Available");
                $(".venue_fields").show();
                $(".noOwnerVenue").hide();
                $(".quickview_body").removeClass("noOwner");
                hideShowResetButton();

            },
            error:function (xhr, ajaxOptions, thrownError){
                if(xhr.status==404) {
                    $("#owners-content").find("#ownerlanguage option:selected").prop("selected", false);
                    localStorage.setItem("ownerAvailability","notAvailable");
                    localStorage.removeItem("username");
                    localStorage.removeItem("subscription");
                    $("#ownerStatus option[value='OWNER']").prop('selected', true);
                    $("#ownerlanguage option[value='FR']").prop('selected', true);
                    $('#userProfile').attr('src', "");
                                    
                    $(".quickview_body").addClass("noOwner");
                    $("#originNoOwner").attr("disabled", true);
                    load_subscriptions(localStorage.getItem("subscriptionCustomerId"));
                    $("#id_customer").val(localStorage.getItem("subscriptionCustomerId"));

                    $("#ownerName").val("");
                    $("#ownerUsername").val("")
                }
            }
        })

        $(".connect_owner").click(function(){
            $('a[href="#owner"]').trigger("click")
        })
        // get venue list
        var all_places_by_ids = {};
        $('#id_place').select2({
            allowClear: true,
            width: '100%',
            placeholder: 'Select Establishment for Owner...',

            dropdownParent: $('#place_selector'),
            ajax: {
                url: "/ajax/autocomplete/place/published/list",
                dataType: 'json',
                delay: 250,
                processResults: function (data, params) {
                    for (var i in data.items){
                        var item0 = data.items[i];
                        all_places_by_ids[item0.id] = item0;
                    }
                    params.page = params.page || 1;
                    return {
                        results: $.map(data.items, function(item){
                            if (item.name){
                                item.text =  item.name + " , " + item.street_address + item.zip_code + item.city + item.country;
                                return item;
                            }
                        }),
                    };
                },
            },
            cache: true,
        });

        $('#id_place').change(function(){
            $(".venueAction").removeClass("d-none")
        })
        


        $('#id_customer').change(function(){
                customer_id = $('#id_customer').val();
                
                load_subscriptions(customer_id);
                if ($('#id_customer').val() == ''){
                $('#id_subscription').val(null).trigger('change');
            }
        });

        
    }

    $("#ownerStatus").change(function(){
        if($("#ownerStatus option:selected").val() !== "OWNER"){
            $("#ownerStatusWarning").modal("show")
            $("#ownerStatus option[value='OWNER']").prop('selected', true);
        }
    })

    $('#id_subscription').on('select2:select', function (e) {
        if(e.params.data.id){
            var subscriptionId = e.params.data.id;
            $.ajax({
                url: '/right-panel/check-subscription/?subscription=' + subscriptionId,
                type: 'get',
                success: function(response){
                    if(response.count > 0){
                        if(response.results[0].subscription == subscriptionId){                    
                            $('.subscrptionalreadyUsed').show();
                            $("#post-edit").attr("disabled",true);
                        }
                    }else{                  
                        $('.subscrptionalreadyUsed').hide();
                        $("#post-edit").attr("disabled",false);
                    }
                },
                error:function (xhr, ajaxOptions, thrownError){
                    if(xhr.status==400) {
                        $('.subscrptionalreadyUsed').hide();
                        $("#post-edit").attr("disabled",false);
                    }
                }    
            });
        }
    });

    var validExtraEmail = true;
    var emailHasMatch = false;
    var validEmail = true;

    function emailValidation() {
        var $ownerEmail = $('#ownerEmail');

        validEmail = checkEmpty($ownerEmail) || checkEmail($ownerEmail);

        if (!validEmail) {
            $(".invalidEmail").show();
            $("#post-edit").attr("disabled",true);
        }

        var ownerEmail = $ownerEmail.val();
        $.ajax({
            url: "/right-panel/user-by-email/",
            data: {
                'email' : ownerEmail
            },
            dataType: 'json',
            success: function(data) {
                for (var i = 0; i < data.results.length; ++i) {

                    var emailCheck = data.results[i];

                    if(emailCheck.email == ownerEmail){
                        emailHasMatch = true;
                        $(".emailAlreadyExist").show();
                        $(".ownerused").show();
                        $("#post-edit").attr("disabled",true);
                        $(".ownerAlreadyUsedEmail").text(ownerEmail);
                        $(".postByOwner").text(emailCheck.post_number)
                        $(".ownerAlreadyUsedEmail").attr("href","/user/edit/"+emailCheck.id);
                        $(".emailNotAlreadyExist").hide();
                        $(".invalidEmail").hide();
                    }else{
                        $(".emailAlreadyExist").hide();
                        $(".ownerused").hide();

                        if (!usernameHasMatch && validEmail) {
                            $("#post-edit").attr("disabled",false);
                        }
                    }

                    // if(emailCheck.status == 10){
                    //     $("#ownerStatus option[value='USER']").prop('selected', true);
                    // }
                    // else if(emailCheck.status == 60){
                    //     $("#ownerStatus option[value='SUBMITTER']").prop('selected', true);
                    // }
                    // else if(emailCheck.status == 40){
                    //     $("#ownerStatus option[value='OWNER']").prop('selected', true);
                    // }
                    // else if(emailCheck.status == 50){
                    //     $("#ownerStatus option[value='VIEWER']").prop('selected', true);
                    // }
                    // else if(emailCheck.status == 20){
                    //     $("#ownerStatus option[value='EDITOR']").prop('selected', true);
                    // }
                    // else if(emailCheck.status == 30){
                    //     $("#ownerStatus option[value='ADMINISTRATOR']").prop('selected', true);
                    // }
                }

                if(data.results.length == 0 && validEmail){
                    emailHasMatch = false;
                    $(".emailAlreadyExist").hide();
                    $(".invalidEmail").hide();
                    $(".ownerused").hide();
                    $(".emailNotAlreadyExist").show();

                    if (!usernameHasMatch && validEmail) {
                        $("#post-edit").attr("disabled",false);
                    }

                }else{
                    $(".emailNotAlreadyExist").hide();
                }

            },
            error: function(data){
                //error
            }
        });

    }

    $('#ownerEmail').on('change', function() {
        emailValidation();
    });

    $('#ownerExtraEmail').on('change', function() {
        validExtraEmail = checkEmpty($('#ownerExtraEmail')) || checkEmail($('#ownerExtraEmail'));

        if (!validExtraEmail) {
            $(".invalidExtraEmail").show();
            $("#post-edit").attr("disabled",true);
        } else {
            $(".invalidExtraEmail").hide();
            $("#post-edit").attr("disabled",false);
        }
    });

    $('#id_customer').on('change', function() {
        $(".requiredCustomerID").hide();
    });

    $('#ownerEmail').on('change', function() {
        $(".requiredEmail").hide();
    });


    $('#id_subscription').on('change', function() {
        $(".requiredSubscription").hide();
    });


    




    $('#id_place').on('change', function() {
        $(".requiredVenue").hide();
    });

    var usernameHasMatch = false;

    $('#ownerUsername').on('change', function() {
        var ownerUsername = $(this).val();
        $(".requiredUsername").hide();

        $.ajax({
            url: "/right-panel/user-by-email/",
            data: {
                'username' : ownerUsername
            },
            dataType: 'json',
            success: function(data) {
                for (var i = 0; i < data.results.length; ++i) {

                    var usernameCheck = data.results[i];

                    if(usernameCheck.username == ownerUsername){
                        usernameHasMatch = true;
                        $(".usernameAlreadyExist").show();
                        $(".ownersusernameused").show();
                        $("#post-edit").attr("disabled",true);
                        $(".ownerAlreadyUsedUsername").text(ownerUsername);
                        $(".postByOwner").text(usernameCheck.post_number)
                        $(".ownerAlreadyUsedUsername").attr("href","/user/edit/"+usernameCheck.id);
                        $(".usernameNotAlreadyExist").hide();
                    }else{
                        $(".usernameAlreadyExist").hide();
                        $(".ownersusernameused").hide();

                        if (!emailHasMatch && validEmail) {
                            $("#post-edit").attr("disabled",false);
                        }
                    }
                }


                if(data.results.length == 0){
                    usernameHasMatch = false;
                    $(".usernameAlreadyExist").hide();
                    $(".ownersusernameused").hide();
                    $(".usernameNotAlreadyExist").show();
                    if (!emailHasMatch && validEmail) {
                        $("#post-edit").attr("disabled",false);
                    }

                }else{
                    $(".usernameNotAlreadyExist").hide();
                }

            },
            error: function(data){
                //error
            }
        });
    });


    function checkEmail(obj) {
        var result = true;

        var email_regex = /^([a-zA-Z0-9_.+-])+\@(([a-zA-Z0-9-])+\.)+([a-zA-Z0-9]{2,3})+$/;
        result = email_regex.test($(obj).val());

        return result;
    }


    function checkEmpty(obj) {
        return obj.val() == "";
    }


    function addUser(venueId) {   
        var addUserURL = '/right-panel/user-by-email/',
            id_place,
            id_subscription,
            fileSelect = document.getElementById('fileUpload'),
            files = fileSelect.files,
            file = files[0],
            data = new FormData();
            addUserXHR = new XMLHttpRequest();

        var requiredEmail = checkEmpty($('#ownerEmail')),
            requiredUsername = checkEmpty($('#ownerUsername')),
            requiredCustomerID = checkEmpty($('#id_customer')),
            requiredSubscription = !$('#id_subscription option:selected').val(),
            requiredVenue = !$('#id_place option:selected').val();

        if (requiredEmail || requiredUsername || requiredCustomerID || requiredSubscription || requiredVenue) {
            $("#sidebarStatus").hide();

            if(requiredEmail) {
                $(".requiredEmail").show();
            }

            if (requiredUsername) {
                $(".requiredUsername").show();
            }

            if (requiredCustomerID) {
                $(".requiredCustomerID").show();
            }

            if (requiredSubscription) {
                $(".requiredSubscription").show();
            }

            if (requiredVenue) {
                $(".requiredVenue").show();
            }

            return;
        }

        // if($("#id_place option:selected").val() === "true"){
        //     id_place = venueId;
        // }else{
        //     id_place = $("#id_place").find("option:selected").val();
        // }

        id_place = $("#id_place").find("option:selected").val();

        id_subscription =  $('#id_subscription').find("option:selected").val()

        $("#nameOfVenue").text(id_place);

        var length = 8,
            charset = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789",
            retVal = "";
        for (var i = 0, n = charset.length; i < length; ++i) {
            retVal += charset.charAt(Math.floor(Math.random() * n));
        }

        data.append("email", $("#ownerEmail").val());
        data.append("full_name", $("#ownerName").val());
        data.append("password", retVal);
        data.append("username", $("#ownerUsername").val());
        data.append("secondary_emails", $("#ownerExtraEmail").val());
        data.append("website_url", $("#ownerWebsite").val());
        data.append("lang",$("#ownerlanguage option:selected").val());
        data.append("type",  40);
        data.append("status", 10);
        data.append("customer", $("#id_customer").val());
        data.append("place_id", id_place);
        data.append("subscription", id_subscription);

        if(fileSelect.value != ''){
            data.append('profile_photo', file, file.name);
        }
            

        addUserXHR.open('POST', addUserURL, true);

        function setHeaders(headers){
            for(let key in headers){
                addUserXHR.setRequestHeader(key, headers[key]);
            }
        }

        setHeaders({"X-CSRFToken":getCookie("csrftoken")})

        addUserXHR.onload = function () {
            if (addUserXHR.status === 201) {
                $("#sidebarStatus").hide();
                $(".emailNotAlreadyExist").hide();
                $(".usernameNotAlreadyExist").hide();
            }
            if (addUserXHR.status === 200 || addUserXHR.status === 201) {
                localStorage.setItem("ownerAvailability","Available");
                $(".quickview_body").removeClass("noOwner");
                $(".venue_fields").show();
                $(".noOwnerVenue").hide();
                $(".usernameNotAlreadyExist").hide();
                $(".emailNotAlreadyExist").hide();


                b_datatable_in_trial.ajax.reload();
                b_datatable_subscribers.ajax.reload();
                b_datatable_all.ajax.reload();
                b_datatable_free.ajax.reload();
                b_datatable_not_connected.ajax.reload();
                b_datatable_stickers.ajax.reload();
            }
        };

        addUserXHR.send(data); 
    }

    var readURL = function(input) {
        if (input.files && input.files[0]) {
            var reader = new FileReader();

            reader.onload = function (e) {
                $('#userProfile').attr('src', e.target.result);
                
                localStorage.setItem("profile_pic",reader.result)
            }
    
            reader.readAsDataURL(input.files[0]);          

        }
    }
    

    $("#fileUpload").on('change', function(){
        readURL(this);
        $('.getfromlocal').attr('src', localStorage.getItem("profile_pic"))
    });

    $('#ownerlanguage').on('change', function(){
        if($(this).val() === "JA" && $("#ownerStatus option:selected").val() === "OWNER") {
            $(".invalidLanguage").show();
            $("#post-edit").attr("disabled",true);
        } else {
            $(".invalidLanguage").hide();
            $("#post-edit").attr("disabled",false);
        }
    });


    function updateOwnerData(venueId){
        var ownerURL = '/right-panel/place/owner/edit/' + venueId,
            //id_place = venueId,
            id_subscription_update,
            data = new FormData(),
            fileSelect = document.getElementById('fileUpload'),
            files = fileSelect.files,
            file = files[0],
            ownerXHR = new XMLHttpRequest();

        if(fileSelect.value != ''){
            data.append('profile_photo', file, file.name);
        }

        id_place = $('#id_place').find("option:selected").val();

        id_subscription_update =  $('#id_subscription').find("option:selected").val()
            
        data.append("email", $("#ownerEmail").val());
        data.append("full_name", $("#ownerName").val());
        data.append("username", $("#ownerUsername").val());
        data.append("secondary_emails", $("#ownerExtraEmail").val());
        data.append("website_url", $("#ownerWebsite").val());
        data.append("lang",  $("#ownerlanguage option:selected").val());
        data.append("origin", $("#origin option:selected").val());
        data.append("type", $("#ownerStatus option:selected").val());
        data.append("customer_id", $("#id_customer").val());
        data.append("subscription_id", id_subscription_update);
        data.append("venue_id", id_place);
            
        ownerXHR.open('PATCH', ownerURL, true);

        function setHeaders(headers){
            for(let key in headers){
                ownerXHR.setRequestHeader(key, headers[key]);
            }
        }

        setHeaders({"X-CSRFToken":getCookie("csrftoken")})

        ownerXHR.onload = function () {

            if (ownerXHR.status === 200 ){
                b_datatable_in_trial.ajax.reload();
                b_datatable_subscribers.ajax.reload();
                b_datatable_all.ajax.reload();
                b_datatable_free.ajax.reload();
                b_datatable_not_connected.ajax.reload();
                b_datatable_stickers.ajax.reload();
            }



            if (ownerXHR.status === 200 || ownerXHR.status === 404 || ownerXHR.status === 500 || ownerXHR.status === 400) {
                $("#sidebarStatus").hide();
            }

            if (ownerXHR.status === 400 && $("#ownerlanguage option:selected").val() === "JA" && $("#ownerStatus option:selected").val() === "OWNER") {
                $(".invalidLanguage").show();
            } else {
                $(".invalidLanguage").hide();
            }
        };
        ownerXHR.send(data);

    }

    // get subscription tab data
    function getSubscriptionData(venueId){
        var $ownerEmail = $("#ownerEmail");

        $.ajax({
            url: '/right-panel/place/subscription/' + venueId,
            type: 'GET',
            success: function(response){
                if(response.customer.id == null){
                    $("#customerId").text("-");

                    if(localStorage.getItem("ownerAvailability") === "notAvailable"){
                        $("#id_customer").val("");
                    }
                }else{
                    $("#customerId").text(response.customer.id);
                    localStorage.setItem("subscriptionCustomerId",response.customer.id);

                    if(localStorage.getItem("ownerAvailability") === "notAvailable"){
                        load_subscriptions(response.customer.id);
                        $("#id_customer").val(response.customer.id);
                    }
                }

                
                if(response.subscription_url == null){
                    $("#customerId").attr("href","#");
                    $("#subscriptionPlan").attr("href","#");   
                    $("#locale").attr("href","#");   
                    $("#trialRemaining").attr("href","#"); 
                    $("#billingDate").attr("href","#"); 
                    $("#billingAmount").attr("href","#"); 

                    
                }else{
                    $("#customerId").attr("href",response.subscription_url)
                    $("#subscriptionPlan").attr("href",response.subscription_url);
                    $("#locale").attr("href",response.subscription_url);
                    $("#trialRemaining").attr("href",response.subscription_url);
                    $("#billingDate").attr("href",response.subscription_url); 
                    $("#billingAmount").attr("href",response.subscription_url); 
                }

                if (response.id) {
                    var option_subscription = new Option(response.id, response.id, true);
                    $("#id_subscription").append(option_subscription).trigger('change');
                }
                if(response.customer.first_name == null){
                    $("#firstName").text("-");
                }else{
                    $("#firstName").text(response.customer.first_name);
                }
                if(response.customer.last_name == null){
                    $("#lastName").text("-");
                }else{
                    $("#lastName").text(response.customer.last_name);
                }
                if(response.customer.company == null){
                    $("#company").text("-");
                }else{
                    $("#company").text(response.customer.company);
                }
                if(response.customer.email == null){
                    $("#emailId").text("-");
                }else{
                    $("#emailId").text(response.customer.email);
                }
                if(response.customer.phone == null){
                    $("#phone").text("-");
                }else{
                    $("#phone").text(response.customer.phone);
                }
                if(response.shipping_address == null){
                    $("#shippingAddress").text("-");
                }else{
                    var line1 = response.shipping_address.line1 ? response.shipping_address.line1 + ",<br>" : "";
                    var line2 = response.shipping_address.line2 ? response.shipping_address.line2 + ",<br>" : "";
                    var line3 = response.shipping_address.line3 ? response.shipping_address.line3 + ",<br>" : "";
                    var city = response.shipping_address.city ? response.shipping_address.city + ",<br>" : "";
                    var zip = response.shipping_address.zip ? response.shipping_address.zip + ",<br>" : "";
                    var country = response.shipping_info_country ? response.shipping_info_country + ",<br>" : "";
                    var state = response.shipping_address.state ? response.shipping_address.state : "";

                    $("#shippingAddress").html(line1 + line2 + line3 + city + zip + country + state);
                }            
                if(response.customer.locale == null){
                    $("#locale").text("-");
                }else{
                    $("#locale").text(response.customer.locale);
                }
                if(response.billing_info_country == null || response.customer.vat_number == null || response.customer.billing_address == null){
                    $("#billingInfo").text("-");
                }else{
                    $("#billingInfo").text(  response.billing_info_country +  " " +  response.customer.billing_address.country + " | " +  response.customer.vat_number);
                }
                if(response.payment_source == null){
                    $("#paymentMethod").text("-");
                }else{
                    $("#paymentMethod").text(response.payment_source.card.brand + " ending " + response.payment_source.card.last4 );
                }
                if(response.status == null){
                    $("#subscriptionStatus").text("-");
                }else{
                    $("#subscriptionStatus").text(response.status);

                    if(response.status == "in_trial"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-in-trial btn btn-xs")
                    }
                    else if(response.status == "future"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-future btn btn-xs")
                    }
                    else if(response.status == "active"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-active btn btn-xs")
                    }
                    else if(response.status == "non_renewing"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-non-renewing btn btn-xs")
                    }
                    else if(response.status == "paused"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-paused btn btn-xs")
                    }
                    else if(response.status == "cancelled"){
                        $("#subscriptionStatus").attr("class", "btn-cgb-cancelled btn btn-xs")
                    }
                }
                if(response.plan_id == null){
                    $("#subscriptionPlan").text("-");
                }else{
                    $("#subscriptionPlan").text(response.plan_id);
                }
                if(response.plan_unit_price == null){
                    $("#subscriptionPlanAmount").text("-");
                }else{
                    $("#subscriptionPlanAmount").text(response.currency_code + " " + response.plan_unit_price / 100);
                }
                if(response.next_billing_at == null){
                    $("#billingDate").text("-");
                }else{
                    $("#billingDate").text(dateFormat(response.next_billing_at));
                }
                // if(response.plan_unit_price == null){
                //     $("#billingAmount").text("-");
                // }else{
                //     $("#billingAmount").text(response.plan_unit_price / 100);
                // }
                if (response.auto_collection) {
                    if (response.auto_collection === "n.d." && response.customer.auto_collection) {
                        $("#autoCollection").text(response.customer.auto_collection);
                    } else {
                        $("#autoCollection").text(response.auto_collection);
                    }
                } else {
                    $("#autoCollection").text("-");
                }
                if(response.event_based_addons == null){
                        $("#addons").text("-");
                }else{
                    var addons = document.getElementById("addons");
                    addons.innerHTML = "";
                    for (var i = 0; i < response.event_based_addons.length; i++) {
                        addons.innerHTML +=  '➜ ' + response.event_based_addons[i].id + '<br>';
                    }
                }
                if(response.trial_end == null) {
                    $("#trialRemaining").text("-");
                }else{
                    var date1 = new Date();
                    var date2 = new Date(response.trial_end);
                    var Difference_In_Time = date2.getTime() - date1.getTime();
                    var Difference_In_Days = Difference_In_Time / (1000 * 3600 * 24);
                    $("#trialRemaining").text(parseInt(Difference_In_Days) + " days");
                }
                if(response.trial_end == null) {
                    $("#trialEnds").text("-");
                }else{
                    $("#trialEnds").text(dateFormat(response.trial_end));
                }
                // if (response.id && !$("#id_subscription").val()) {
                //     var optionSubscriptionId = new Option(response.id, true, true);

                //     $("#id_subscription").append(optionSubscriptionId).trigger('change');
                //     $("#id_subscription").trigger({
                //         type: 'select2:select',
                //         params: {
                //             data: response
                //         }
                //     });
                // }
                const ownerAvailability = localStorage.getItem("ownerAvailability");

                if (response.customer) {
                    if (ownerAvailability === "notAvailable") {
                        $ownerEmail.val(response.customer.email);
                        emailValidation();
                    }
                    if (response.customer.id && !$("#id_customer").val()) {
                        $("#id_customer").val(response.customer.id);
                    }
                }

            }
        });
    }
    // open right panel and get data

    $(document).on('click','.editVenue,.editOwner',function(e){
        $("#sidebarStatus").show()
        // e.stopPropagation();
        $('.sidebar_quickview').addClass('reveal');
        venueId = $(this).data('id');
        $('.sidebar_quickview').attr('id',venueId);
        localStorage.setItem("venueId",venueId)
        activeVenueId = localStorage.getItem("venueId")
        getVenueData(activeVenueId)
        getWineData()
        getWineScore()
        getImages(activeVenueId)
        getOwnerData(activeVenueId)
        getSubscriptionData(activeVenueId);
    })

    $(document).on('click','.editVenue',function(e){
        $("a[href='#venue']").trigger("click")
    })
    

    $(document).on('click','.editOwner',function(e){
        $("a[href='#owner']").trigger("click")
    })   


    var addressChanged = 0;

    $(document).on('change','.pac-target-input',function(){
        addressChanged = 1;
    });

    $("#post-edit").on("click",function(){
        $("#sidebarStatus").show()   
        updateVenueData(activeVenueId);

        if(addressChanged == 1){
            $("#addressLine").removeClass('error_autocomplete');
            $(".form-control").removeClass('error_autocomplete');
        }
    })


    var username =localStorage.getItem("username");
    var modalIsOpen = false;
    
    $("#btn_renew_password").on("click",function(){
        modalIsOpen = true;
        var jsonArray = {
            "username": username,
        };

        $.ajax({
                type: "POST",
                dataType: "json",
                url: "/ajax/users/resetpass",
                data: jsonArray,
                success: function(data) {
                    $("#modal_renew_password").modal("toggle");
                },
                error: function(data){
                    console.warn(data);
                }
        });
    });

    $("#btn_resend_activation").on("click",function(){
        modalIsOpen = true;
        var jsonArray = {
            "username": username,
            "action": "resend_activation"
        };

        $.ajax({
                type: "POST",
                dataType: "json",
                url: "/ajax/users/resetpass",
                data: jsonArray,
                success: function(data) {
                    $("#modal_resend_activation").modal("toggle");
                },
                error: function(data){
                    console.warn(data);
                }
        });
    });

    $("#myModalMap,#ownerStatusWarning").on("click",function(){
        modalIsOpen = true;
    }); 

    // close right panel

    $('#main-wrapper').click( function() {
        if (!modalIsOpen) {
            $('.sidebar_quickview').removeClass('reveal');
            $(".emailAlreadyExist").hide();
            $(".emailNotAlreadyExist").hide();
            $(".usernameAlreadyExist").hide();
            $(".usernameNotAlreadyExist").hide();
            $(".ownerused").hide();
            $(".ownersusernameused").hide();
            $("#post-edit").attr("disabled",false);
            $("#id_place").text("");
            $("#id_subscription").text("");
            $("#ownerEmail").val(null);
            $("#id_customer").val(null);
            modalIsOpen = false;
        }
    });

    
    $('.quickview_footer > .btn-cancel').on("click",function(){
        if (!modalIsOpen) {
            $(this).parents('.sidebar_quickview').removeClass('reveal date_selected');
        }
    });

    $('.closePanel,.quickview_footer > .btn-cancel').on("click",function(){
        $(this).parents('.sidebar_quickview').removeClass('reveal date_selected');
        $(".emailAlreadyExist").hide();
        $(".emailNotAlreadyExist").hide();
        $(".usernameAlreadyExist").hide();
        $(".usernameNotAlreadyExist").hide();
        $(".ownerused").hide();
        $(".ownersusernameused").hide();
        $("#post-edit").attr("disabled",false);
        $("#id_place").text("");
        $("#id_subscription").text("");
        $("#ownerEmail").val(null);
        $("#id_customer").val(null);
    })

    $('button.resetButton').click(function(){
        $(this).next().val("");
        $(this).hide();
    });

    $('#Venue-content input').on('input',function(){
        if($(this).val() !== ""){
            $(this).prev().show();
        }else{
            $(this).prev().hide();
        }
    });

    $('#owners-content input').on('input',function(){
        if($(this).val() !== ""){
            $(this).prev().show();
        }else{
            $(this).prev().hide();
        }
    });
});