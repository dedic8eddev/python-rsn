var b_datatable_places = null;

init.push(function () {
    b_datatable_places = $('#jq-datatables-places').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,

        ajax: $.fn.dataTable.pipeline({
            "url": url_userplace_items_ajax,
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
            { "data" : "expert_img_html" },

            { "data" : "name" },
            { "data" : "street_address" },
            { "data" : "zip_code" },
            { "data" : "city" },
            { "data" : "country" },
            { "data" : "email" },
            { "data" : "type_text", orderable: false },
            { "data" : "website_url_link", orderable: false },
            { "data" : "status_text" },
            { "data" : "social_links", orderable: false },
            { "data" : "sticker" }
        ],
        drawCallback: function(settings) {

            $('[data-toggle="tooltip"]').tooltip();

            setHandleActionFooterTable('jq-datatables-places', 'toggle-all-places', 'action_userplaces');

            $("#jq-datatables-places img:visible").unveil();

            // b_datatable_places.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_places.data().search();

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places_wrapper .table-caption').text('Places reviewed - ' +
                    search_value + " : " + total_records);
            }else{
                $('#jq-datatables-places_wrapper .table-caption').text('Places reviewed : ' + total_records);
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

    $('#jq-datatables-places_wrapper .table-caption').text('Places reviewed');
    $('#jq-datatables-places_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    setHandleActionFooterTableToggleAll('toggle-all-places', 'jq-datatables-places', 'toggle-all-places', 'action_userplaces');

    $("#ui-bootbox-publish_userplaces").click(function(){
        massOperationPipelineTable(url_places_publish_ajax, 'places', 'jq-datatables-places');
    });

    $("#ui-bootbox-unpublish_userplaces").click(function(){
        massOperationPipelineTable(url_places_unpublish_ajax, 'places', 'jq-datatables-places');
    });

    $("#ui-bootbox-indoubt_userplaces").click(function(){
        massOperationPipelineTable(url_places_set_in_doubt_ajax, 'places', 'jq-datatables-places');
    });

    $("#ui-bootbox-close_userplaces").click(function(){
        massOperationPipelineTable(url_places_close_ajax, 'places', 'jq-datatables-places');
    });

    $("#ui-bootbox-delete_userplaces").click(function(){
        massOperationConfirmPipelineTable(url_places_delete_ajax, 'jq-datatables-places',
            'action_delete_confirm_userplaces', 'ui-bootbox-delete-confirm-userplaces', 'ui-bootbox-delete-cancel-userplaces');
    });

    $("#ui-bootbox-duplicate").click(function(){
        massOperationPipelineTable(url_places_duplicate_ajax, 'places', 'jq-datatables-places');
    });

    $("#ui-bootbox-cancel_userplaces").click(function(){
        cancelSelectionActionPanelId("action_userplaces");
    });

    $("#jq-datatables-places_filter  .form-control.input-sm[type='search']").unbind();
    $("#jq-datatables-places_filter  .form-control.input-sm[type='search']").bind('keyup', function(e) {
        if (this.value.length > 2 || this.value.length === 0) {
            b_datatable_places.search(this.value).draw(true);
        }
    });

    $(document).on('click', '#clear-search', function() {
        $(".form-control.input-sm[type='search']").val('');
        b_datatable.search('').draw(true);
    });

});
