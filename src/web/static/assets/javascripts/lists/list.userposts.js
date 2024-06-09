var b_datatable_posts = null;

//function massOperationTableReviews(url, entities, extraSerArray) {
//    return massOperationTable(url, entities, 'jq-datatables-example', extraSerArray);
//}


init.push(function () {
    $(document).on('click', '#clear-search', function() {
        $(".form-control.input-sm[type='search']").val('');
        b_datatable.search('').draw(true);
    });

    if (user_is_admin) {
        var columns_all = [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "img_html", orderable: false },
            { "data" : "date" },

            { "data" : "title" },
            { "data" : "description", orderable: false },
            { "data" : "status_html" },

            { "data" : "designation" },
            { "data" : "grape_variety" },
            { "data" : "winemaker" },
            { "data" : "year" },

            { "data" : "color_text" },
            { "data" : "sparkling_html" },

            { "data" : "comment_number" },
            { "data" : "likevote_number" },
            { "data" : "drank_it_too_number" }
        ];
    } else {
        var columns_all = [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "img_html", orderable: false },
            { "data" : "date" },

            { "data" : "title" },
            { "data" : "description", orderable: false },
            { "data" : "status_html" },

            { "data" : "designation" },
            { "data" : "grape_variety" },
            { "data" : "year" },

            { "data" : "color_text" },
            { "data" : "sparkling_html" },

            { "data" : "comment_number" },
            { "data" : "likevote_number" },
            { "data" : "drank_it_too_number" }
        ];
    }

    b_datatable_posts = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,
        "paging": true,

        ajax: $.fn.dataTable.pipeline({
            "url": url_userpost_items_ajax,
            "type" : "POST",
            //"data": function (d) {
            //    d.extra_search = $('#extra').val();
            //}
        }),

        'bAutoWidth' : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

        "order": [[ 2, "desc" ]],

        columns: columns_all,
        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();
            setHandleActionFooterTable('jq-datatables-example', 'toggle-all', 'action');
            $("#jq-datatables-example img:visible").unveil();
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_posts.data().search();

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example_wrapper .table-caption').text('Posts reviewed - ' +
                    search_value + " : " + total_records);
            }else{
                $('#jq-datatables-example_wrapper .table-caption').text('Posts reviewed : ' + total_records);
            }

            if (search_value != undefined && search_value != null && search_value != "") {
                $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            } else {
                $('.clear-search').remove();
            }

            $('#jq-datatables-example_wrapper .table-caption').text('Posts reviewed');
            $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

            setHandleActionFooterTableToggleAll('toggle-all', 'jq-datatables-example', 'toggle-all', 'action');

            mass_operation_table_id = "jq-datatables-example";

            $("#ui-bootbox-publish").click(function(){
                massOperationPipeline(url_wineposts_publish_ajax, null);
                return false;
            });

            $("#ui-bootbox-unpublish").click(function(){
                massOperationPipeline(url_wineposts_unpublish_ajax, null);
                return false;
            });

            $("#ui-bootbox-indoubt").click(function(){
                massOperationPipeline(url_wineposts_set_in_doubt_ajax, null);
                return false;
            });

            $("#ui-bootbox-bioorg").click(function(){
                massOperationPipeline(url_wineposts_set_bio_organic_ajax, null);
                return false;
            });
            
            $("#ui-bootbox-refuse").click(function(){
                massOperationConfirmPipeline(url_wineposts_refuse_ajax,
                     'action_refuse_confirm', 'ui-bootbox-refuse-confirm', 'ui-bootbox-refuse-cancel', null);
                return false;
            });

            $("#ui-bootbox-delete").click(function(){
                massOperationConfirmPipeline(url_wineposts_delete_ajax,
                     'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', null);
                return false;
            });

            $("#ui-bootbox-undelete").click(function(){
                massOperationPipeline(url_wineposts_undelete_ajax, 'wineposts');
            });

            $("#ui-bootbox-cancel").click(function(){
                cancelSelection();
                return false;
            });

            $("#jq-datatables-example_filter  .form-control.input-sm[type='search']").unbind();
            $("#jq-datatables-example_filter  .form-control.input-sm[type='search']").bind('keyup', function(e) {
                if (this.value.length > 2 || this.value.length === 0) {
                    b_datatable_posts.search(this.value).draw(true);
                }
            });

            mop_init(massOperationPipeline);

            var paginate_button_count = $(".paginate_button").not(".paginate_button.previous").not(".paginate_button.next").length;
            if (paginate_button_count < 2){
                $(".paginate_button").hide();
            }else{
                $(".paginate_button").show();
            }
        }
    });



});

init.push(function () {
    $('[data-toggle="tooltip"]').tooltip();
});
