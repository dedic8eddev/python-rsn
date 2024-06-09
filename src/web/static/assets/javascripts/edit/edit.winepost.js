var pdg_widget = null;
var pixie = null;
var select_wm_winepost = null;
var select_wm = null;
var select_wine = null;
var all_winemakers_by_ids = {};
var image_manager_wm_files = null;
var b_dropzone_wm_files = null;

function loadRelatedLists(){
    loadAndInsertHtmlByAjax(ajax_related_lists_url, "related_lists");
}


// vuforia -> edit.winepost.vuforia.js
// original winemaker handling -> edit.winepost.original-winemaker.js


init.push(function () {
  console.log('heeeere')
    if (!is_new) {
        loadRelatedLists();
    }
    $("#btn-save").unbind('click');
    $("#btn-save").click(function(){
        var future_status = $("#id_status").val();
        if(!$("#id_is_parent_post").prop('checked') && is_draft && future_status == 20 ) {
            $("#modal_is_pp").modal();
            return false;
        }
    });
});


// file handling -> edit.winepost.files.js
// places handling -> edit.winepost.places.js


init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
});


// wm-winepost, define as children (main_wp), parent post (main_wp) -> edit.winepost.parent.child.js
// yearly data handling -> edit.winepost.yearly-data.js


function get_basename(path) {
    var index = path.lastIndexOf('/');
    if(index == -1) {
        return path;
    }else {
        return path.substring(index + 1);
    }
}


var baseUrl = (window.location).href;
var winePostId = baseUrl.substring(baseUrl.lastIndexOf('/') + 1);


// ===== natural/other for MAIN WINEPOST =====
init.push(function(){
    $("[name='nat_oth_main_wp']").click(function(){
        var which = $("[name='nat_oth_main_wp']:checked").val();
        if(which == 'natural') {
            sel_display_natural = true;
            $(".display-natural").show();
            $(".display-other").hide();
        } else {
            sel_display_natural = false;
            $(".display-natural").hide();
            $(".display-other").show();
        }
    });
});
// ===== /natural/other for MAIN WINEPOST =====




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
        url: "/ajax/admincomments/winemaker/" + winePostId + "/",
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
        url: "/ajax/admincomments/winemaker/" + winePostId + "/",
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



// pixie -> edit.winepost.vuforia.js
