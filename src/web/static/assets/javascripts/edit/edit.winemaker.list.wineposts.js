init.push(function () {
    if (!is_new) {
        $('#jq-datatables-wineposts').dataTable({
            ajax: {
                "url": url_get_winepost_items,
                "type" : "POST",
                "autoWidth": true
                //"data": function (d) {
                //    d.extra_search = $('#extra').val();
                //}
            },
            "aLengthMenu": [ 100, 500, 1000 ],
            columns: [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html", orderarble: false },
                { "data" : "label_img_html", orderarble: false },
                { "data" : "vuforia_img_html", orderarble: false },
                { "data" : "author_img_html" },

                { "data" : "title" },
                { "data" : "status" },
                { "data" : "designation" },

                { "data" : "grape_variety" },
                { "data" : "year" },
                { "data" : "color_text" },
                { "data" : "sparkling_html" },

                { "data" : "comment_number" },
                { "data" : "likevote_number" },
                { "data" : "drank_it_too_number" },
            ],
            drawCallback: function(settings) {
                $('[data-toggle="tooltip"]').tooltip();

                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $('#jq-datatables-wineposts_wrapper .table-caption').text('Registered wines for this winemaker');
//                if((settings.aoData != undefined)&&(settings.aoData != null)&&(settings.aoData.length >0)){
//
//
//                }else{
//                    $('#jq-datatables-wineposts_wrapper .table-caption').text('No registered wines for this winemaker found.');
//                }

                $('#jq-datatables-wineposts_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

                $('#toggle-all').click(function() {
                    $('#jq-datatables-reviews .table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
                    // handleActionFooter();
                });

                $('#jq-datatables-wineposts').wrap('<div style="width: 100%; overflow-x: auto; margin-bottom:10px; "></div>');
                $("#jq-datatables-wineposts img:visible").unveil();

                mop_init(massOperation);

                var paginate_button_count = $(".paginate_button").not(".paginate_button.previous").not(".paginate_button.next").length;
                if (paginate_button_count < 2){
                    $(".paginate_button").hide();
                    //$(".paginate_button.previous").hide();
                    //$(".paginate_button.next").hide();
    //                    $(".paginate_button.active").prop('disabled', true);
                }else{
                    $(".paginate_button").show();
    //                $(".paginate_button.previous").show();
    //                $(".paginate_button.next").show();
    //                    $(".paginate_button.active").prop('disabled', false);
                }
            }
        });

        $('#toggle-all').click(function() {
            $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
            handleActionFooter();
        });

        mass_operation_table_id = "jq-datatables-wineposts";

        $("#ui-bootbox-publish").click(function(){
            massOperation(url_wineposts_publish_ajax, null);
            return false;
        });

        $("#ui-bootbox-unpublish").click(function(){
            massOperation(url_wineposts_unpublish_ajax, null);
            return false;
        });

        $("#ui-bootbox-indoubt").click(function(){
            massOperation(url_wineposts_set_in_doubt_ajax, null);
        });


        $("#ui-bootbox-bioorg").click(function(){
            massOperation(url_wineposts_set_bio_organic_ajax, null);
            return false;
        });

        $("#ui-bootbox-investigate").click(function(){
            massOperation(url_winemakers_set_to_investigate_ajax, null);
            return false;
        });

        $("#ui-bootbox-refuse").click(function(){
            massOperationConfirm(url_wineposts_refuse_ajax,
                 'action_refuse_confirm', 'ui-bootbox-refuse-confirm', 'ui-bootbox-refuse-cancel', null);
            return false;
        });

        $("#ui-bootbox-delete").click(function(){
            massOperationConfirm(url_wineposts_delete_ajax,
                 'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', null);
            return false;
        });

        $("#ui-bootbox-cancel").click(function(){
            cancelSelection();
            return false;
        });
    }
});
