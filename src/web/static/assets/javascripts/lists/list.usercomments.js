var b_datatable_comments = null;

function loadRelatedLists() {
    // TODO
}

function editCommentOpen(id) {
    $("#modal-edit-comment").modal();
    $.ajax({
        type        : "POST",
        url         : url_edit_comment_open,
        data        : {
            "id": id
        },
        dataType    : 'json',
        success: function(data) {
            $("#edited-comment-content").val(data['description']);
            $("#modal-edit-comment").modal();
            $("#edit-comment-update-btn").unbind('click');
            $("#edit-comment-update-btn").click(function() {
                editCommentUpdate(id, $("#edited-comment-content").val());
            });

        },
        error: function(data){
            console.warn(data);
        }
    });
}

function editCommentUpdate(id, description) {
    $.ajax({
        type        : "POST",
        url         : url_edit_comment_update,
        data        : {
            "id": id,
            "description": description
        },
        dataType    : 'json',
        success: function(data) {
            $("#edited-comment-content").val(data['description']);
            $("#modal-edit-comment").modal("hide");
            $("#jq-datatables-comments").DataTable().clearPipeline().draw();
        },
        error: function(data){
            console.warn(data);
        }
    });
}


init.push(function () {
    b_datatable_comments = $('#jq-datatables-comments').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,

        ajax: $.fn.dataTable.pipeline({
            "url": url_usercomment_items_ajax,
            "type" : "POST",
            "data": function (d) {
                d.extra_search = $('#extra').val();
            }
        }),
        bAutoWidth : false,

        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

        "order": [[ 2, "desc" ]],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "name" },
            { "data" : "comment" },
            { "data" : "actions", orderable: false }
        ],
        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();
            setHandleActionFooterTable('jq-datatables-comments', 'toggle-all-comments', 'action_usercomments');
            $("#jq-datatables-comments img:visible").unveil();

            // b_datatable_comments.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_comments.data().search();

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-comments_wrapper .table-caption').text('Comments - ' + search_value + " : " + total_records);
            }else{
                $('#jq-datatables-comments_wrapper .table-caption').text('Comments: ' + total_records);
            }

            if (search_value != undefined && search_value != null && search_value != "") {
                $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            } else {
                $('.clear-search').remove();
            }

            var paginate_button_count = $(".paginate_button").not(".paginate_button.previous").not(".paginate_button.next").length;
            if (paginate_button_count < 2){
                $(".paginate_button").hide();
            }else{
                $(".paginate_button").show();
            }

            // --------- ACTIONS: DELETE COMMENT --------------------------------------------------
            bindSingleOperationConfirm('delete_comment_', url_delete_comment, "erasemessage", "ui-bootbox-delete-comment-one",
                "ui-bootbox-cancel-comment-one", "comments", loadRelatedLists, 'jq-datatables-comments', 'toggle-all-comments', true);
            $("[id^='edit_comment_").unbind('click');
            $("[id^='edit_comment_").click(function() {
                var id = $(this).attr('id').substr(13);
                editCommentOpen(id);
            });

        }
    });

    $('#jq-datatables-comments_wrapper .table-caption').text('Comments');
    $('#jq-datatables-comments_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    setHandleActionFooterTableToggleAll('toggle-all-comments', 'jq-datatables-comments', 'toggle-all-comments', 'action_usercomments');
    //    $("#ui-bootbox-publish_usercomments").click(function(){
    //        massOperationPipelineTable(url_comments_publish_ajax, 'comments', 'jq-datatables-comments');
    //    });
    //    $("#ui-bootbox-unpublish_usercomments").click(function(){
    //        massOperationPipelineTable(url_comments_unpublish_ajax, 'comments', 'jq-datatables-comments');
    //    });
    //    $("#ui-bootbox-indoubt_usercomments").click(function(){
    //        massOperationPipelineTable(url_comments_set_in_doubt_ajax, 'comments', 'jq-datatables-comments');
    //    });
    //    $("#ui-bootbox-close_usercomments").click(function(){
    //        massOperationPipelineTable(url_comments_close_ajax, 'comments', 'jq-datatables-comments');
    //    });
    //    $("#ui-bootbox-delete_usercomments").click(function(){
    //        massOperationConfirmPipelineTable(url_comments_delete_ajax, 'jq-datatables-comments',
    //            'action_delete_confirm_usercomments', 'ui-bootbox-delete-confirm-usercomments', 'ui-bootbox-delete-cancel-usercomments');
    //    });
    //    $("#ui-bootbox-duplicate").click(function(){
    //        massOperationPipelineTable(url_comments_duplicate_ajax, 'comments', 'jq-datatables-comments');
    //    });
    //    $("#ui-bootbox-cancel_usercomments").click(function(){
    //        cancelSelectionActionPanelId("action_usercomments");
    //    });

    $("#jq-datatables-comments_filter  .form-control.input-sm[type='search']").unbind();

    $("#jq-datatables-comments_filter  .form-control.input-sm[type='search']").bind('keyup', function(e) {
        if (this.value.length > 2 || this.value.length === 0) {
            b_datatable_comments.search(this.value).draw(true);
        }
    });

    $(document).on('click', '#clear-search', function() {
        $(".form-control.input-sm[type='search']").val('');
        b_datatable.search('').draw(true);
    });
});
