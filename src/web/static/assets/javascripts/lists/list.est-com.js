var b_datatable = null;

init.push(function () {
    b_datatable = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,

        ajax: $.fn.dataTable.pipeline({
            "url": url_est_com_items_ajax,
            "type" : "POST",
            "data": function (d) {
                d.extra_search = $('#extra').val();
            }
        }),
        'bAutoWidth' : false,

        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

        "order": [[ 1, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html", orderable: true },

            { "data" : "place_img_html", orderable: false },
            { "data" : "place_name", orderable: true },
            { "data" : "description", orderable: true },
            { "data" : "place_status", orderable: true }
        ],

        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });

            $("#jq-datatables-example img:visible").unveil();

//            var total_records = b_datatable.fnSettings().fnRecordsTotal();
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable.data().search();

            var url_free_glass = "";
            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example_wrapper .table-caption').html('<a href="'+url_places+'">LAST PUBLISHED PLACES : ' +
                    total_records_places + '</a> -  <span class="caption-est-comments" >comments - sear</span>');
            }else{
                $('#jq-datatables-example_wrapper .table-caption').html('<a href="'+url_places+'">LAST PUBLISHED PLACES : ' +
                    total_records_places + '</a> -  <span class="caption-est-comments" >comments</span>');
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
        }
    });

    $('#jq-datatables-example_wrapper .table-caption').text('Latest published est. comments');
    $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-unban-user").click(function(){
        massOperationPipeline(url_est_com_unban_user_ajax, 'est-com');
    });


    $("#ui-bootbox-delete").click(function(){
        massOperationConfirmPipeline(url_est_com_delete_ajax,
             'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', 'est-com');
    });

//    $("#ui-bootbox-undelete").click(function(){
//        massOperationPipeline(url_est_com_undelete_ajax, 'est-com');
//    });

    $("#ui-bootbox-ban-user").click(function(){
        massOperationConfirmPipeline(url_est_com_ban_user_ajax,
             'action_ban_user_confirm', 'ui-bootbox-ban-user-confirm', 'ui-bootbox-ban-user-cancel', 'est-com');
    });

    $("#ui-bootbox-cancel").click(function(){
        cancelSelection();
    });

    $(".form-control.input-sm[type='search']").unbind();
    $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
        search_value = this.value;
        if (this.value.length > 2 || this.value.length === 0) {
            b_datatable.search(this.value).draw(true);
        }
    });

    $(document).on('click', '#clear-search', function() {
        $(".form-control.input-sm[type='search']").val('');
        b_datatable.search('').draw(true);
    });
});

init.push(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
