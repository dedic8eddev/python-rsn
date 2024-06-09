var fileSelect = document.getElementById('id_image');
var statusDiv = document.getElementById('status');
var rowResults = document.getElementById('row-results');
statusDiv.style.display = 'none';

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
                                url: '/ajax/ocr-calc-task-result/?winelist_file_id=' + localStorage.getItem("winelist_file_id"),
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
                                    var dataPassed   = {
                                            "winelist_file_id":  wineid,
                                            "is_temp": false,
                                            "is_in_shared_pool":true
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

        var csrf = $("input[name=csrfmiddlewaretoken]").val();

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
                            status = response.ocr_recognize_celery_task_status;
                        },
                        complete: function() {
                            if(status === "SUCCESS"){
                                statusDiv.style.display = 'none';                                    
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
    wl_details_open(wineId);
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

$(document).on("click",".refresh_temp_score",function(){
    wl_refresh_place_score()
})

init.push(function () {
    image_manager_wl = new ImageManager($("#container-current-winelists"), {
        b_sortable: null,
        temp_image_ordering_field: null,
        url_current_images : url_current_winelists_ajax,
        url_delete_image : url_winelist_delete_ajax,
        image_identifier_xhr_field:"id",

        callback: function(){
        }
    });
});

function getpageLink(keyword){
    var arr = [];
    i = 0;
    // $('[data-keyword="'+keyword+'"]').each(function(index, value) {
    //     arr[i++] = {"keyword": $(this).data("keyword"),"link":$(this).data("link")}
   
    //     var keywordListArray = [...new Map(arr.map(item => [item["link"], item])).values()];
    //     console.log(keywordListArray)
    //     var keywordList = "";
    //     $.each(keywordListArray, function(i, item) {
    //         keywordList += '<a href="'+keywordListArray[i].link+'" target="_blank" class="selectedKeyword">'+keywordListArray[i].keyword+'</a><br>'; 
    //     }); 
    //    $('.keywordList').html(keywordList); 
    // });

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
                            //var wineid = response.winelist_file_id;
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
                           console.clear();
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

function getExcludedKeyword() {
    statusDiv.style.display = 'block';
    $.ajax({
        type: "GET",
        url: "/ajax/nwla/excluded-keywords/",
        success: function(response) {
            let data = response.reduce((r, e) => {
                function checkFirstLetterNumber(str) {
                    return /^\d/.test(str);
                }
                function checkFirstLetterSpecial(_string)
                {
                    let spCharsRegExp = /^[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>\/?]+/;
                    return spCharsRegExp.test( _string);
                }
                let group;
                if (e.word[0] == " "){
                    group = e.word[1].toUpperCase();
                }else{
                    group = e.word[0].toUpperCase();
                }
                if(checkFirstLetterNumber(e.word) || checkFirstLetterSpecial(e.word)){
                    group = "hash"
                }
            if(!r[group]) r[group] = {group, children: [e]}
            else r[group].children.push(e);
            return r;
            }, {})

            let result = Object.values(data)

            var keywordHtml = "";
            $.each(result, function(i, item) {
                var groupTitle;
                if(result[i].group == 'hash'){
                    groupTitle =  '#'
                }else{
                    groupTitle = result[i].group 
                }
                keywordHtml += '<div id="'+ result[i].group +'_words">'+
                                '<div class="group_title">' + groupTitle  +'</div>' +
                                    '<ul class="exclude_keyword_list">';
                                        $.each(result[i].children, function(j, item) {
                                            keywordHtml +=  '<li><span>'+ result[i].children[j].word +'</span><i class="fa fa-times-circle delete_keyword" data-id="'+ result[i].children[j].id +'"></i></li>';     
                                        });
                                    keywordHtml += '</ul>'+
                                '</div>';
                                            
                $('a[href="#'+result[i].group+'_words"]').addClass("available");    
            });      
            $('.exclude_keywords').html(keywordHtml);            
            statusDiv.style.display = 'none';
        },
        error: function(data){
            console.warn(data);
        }
    });
}

$(document).ready(function(){
    getExcludedKeyword();
})
function searchKeyword(keyword){
    $('.exclude_keyword_list li').each(function(){
        var lcval = $(this).text().toLowerCase();
        if(lcval.indexOf(keyword)>-1){
            $(this).show();
        } else {
            $(this).hide();
        }
    });
}
$('.searchKeyword').keyup(function(){
    var $this = $(this);
    var value = $this.val().toLowerCase();
    if(value.length > 0){
        $this.next('.clear-search').fadeIn()
        searchKeyword(value)
    }else{
        $this.next('.clear-search').fadeOut()
    }
});
$('.clear-search').click(function(){
    $(this).prev("input").val("");
    $(this).fadeOut();
    searchKeyword("")
})


$(document).on("click",".delete_keyword",function(){
    var $this = $(this);
    $("#deleteKeyword").modal('show');
    localStorage.setItem("excludedKeywordId",$this.data("id"));
})
$('.btn_delete_keyword').click(function(){
    $.ajax({
        type: "DELETE",
        headers: { "X-CSRFToken": getCookie("csrftoken") },
        url: '/ajax/nwla/excluded-keywords/' +  localStorage.getItem("excludedKeywordId"),
        success: function(data) {
            getExcludedKeyword();
        },
        error: function(data){
            console.warn(data);
        }
    });
})
$(".alphabetic_menu a").click(function(){
   $(this).addClass("active");
   $(this).parents("li").siblings("li").find("a").removeClass("active");

})


window.onscroll = function() {myFunction()};

var navbar = document.getElementById("stickyBar");
var sticky = navbar.offsetTop;
function myFunction() {
    if (window.pageYOffset >= 320) {
        navbar.classList.add("sticky")
    } else {
        navbar.classList.remove("sticky");
    }
}

$(document).ready(function(){
    var sectionIds = $('.alphabetic_menu a.available');
    $(document).scroll(function(){
        sectionIds.each(function(){
            var container = $(this).attr('href');
            var containerOffset = $(container).offset().top;
            var containerHeight = $(container).outerHeight();
            var containerBottom = containerOffset + containerHeight;
            var scrollPosition = $(document).scrollTop();
            if(scrollPosition < containerBottom - 20 && scrollPosition >= containerOffset - 20){
                $(this).addClass('active');
            } else{
                $(this).removeClass('active');
            }  
        });
    });
});