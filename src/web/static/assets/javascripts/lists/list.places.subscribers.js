var b_datatable = null;
var table_label = "Latest published subscribers' places: ";

init.push(function () {
    b_datatable = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,

        ajax: $.fn.dataTable.pipeline({
            "url": url_get_place_items_ajax,
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
            { "data" : "owner_img_html" },
            { "data" : "expert_img_html" },

            { "data" : "name" },
            { "data" : "street_address" },
            { "data" : "zip_code" },
            { "data" : "city" },
            { "data" : "country" },
            { "data" : "email" },
            { "data" : "type_text", orderable: false },
            { "data" : "total_wl_score", orderable: true },
            { "data" : "status_text" },
            { "data" : "chargebee_status" },
        ],
        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();
            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-example img:visible").unveil();
            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable.data().search();
            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example_wrapper .table-caption').html(table_label + search_value + " : " + total_records);
                        // + ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>');
                        // + ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }else{
                $('#jq-datatables-example_wrapper .table-caption').html(table_label + total_records);
                        // + ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        // + ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#jq-datatables-example_wrapper .table-caption').text(table_label);
    $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        massOperationPipeline(url_places_publish_ajax, 'places');
    });

    $("#ui-bootbox-unpublish").click(function(){
        massOperationPipeline(url_places_unpublish_ajax, 'places');
    });

    $("#ui-bootbox-indoubt").click(function(){
        massOperationPipeline(url_places_set_in_doubt_ajax, 'places');
    });

    $("#ui-bootbox-close").click(function(){
        massOperationPipeline(url_places_close_ajax, 'places');
    });

    $("#ui-bootbox-delete").click(function(){
        massOperationConfirmPipeline(url_places_delete_ajax,
            'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', 'places');
    });

    $("#ui-bootbox-duplicate").click(function(){
        massOperationPipeline(url_places_duplicate_ajax, 'places');
    });

    $("#ui-bootbox-cancel").click(function(){
        cancelSelection();
    });

    $(".form-control.input-sm[type='search']").unbind();

    $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
        if (this.value.length > 2 || this.value.length === 0) {
            b_datatable.search(this.value).draw(true);
        }
    });

    $(document).on('click', '#clear-search', function() {
        $(".form-control.input-sm[type='search']").val('');
        b_datatable.search('').draw(true);
    });

});
