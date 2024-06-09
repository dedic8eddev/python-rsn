var b_datatable = null;

init.push(function () {
    b_datatable = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 6000,
        "paging": true,

        ajax: $.fn.dataTable.pipeline({
            "url": url_est_free_glass_items_ajax,
            "type" : "POST",
            //"data": function (d) {
            //    d.extra_search = $('#extra').val();
            //}
        }),

        'bAutoWidth' : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "order": [[ 6, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "place_img_html", orderable: false },
            { "data" : "street_address", orderable: true },

            { "data" : "city", orderable: true },
            { "data" : "country", orderable: true },
            { "data" : "name", orderable: true },

            { "data" : "free_glass_last_action_date", orderable: true },
            { "data" : "free_glass_drinks_geolocated", orderable: true },
            { "data" : "free_glass_get_free_glass_button", orderable: false },

            { "data" : "free_glass_got_cnt", orderable: true },
            { "data" : "free_glass_users", orderable: true },
            { "data" : "free_glass_donators", orderable: true }
        ],

        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();

//            $('[name="ids"]').click(function() {
//                handleActionFooter();
//            });

            $("#jq-datatables-example img:visible").unveil();

            // var total_records = b_datatable.fnSettings().fnRecordsTotal();
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable.data().search();

            $('#jq-datatables-example_wrapper .table-caption').html('Places: '
                + total_records_places
                + ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>'
                + ' -  <a class="caption-est-comments" style="font-style: normal;" href="'
                + url_free_glass_event + '">event scheduler</a>');

            if (search_value != undefined && search_value != null && search_value != "") {
                $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            } else {
                $('.clear-search').remove();
            }

            var paginate_button_count = $(".paginate_button").not(".paginate_button.previous")
                .not(".paginate_button.next").length;
            if (paginate_button_count < 2){
                $(".paginate_button").hide();
            }else{
                $(".paginate_button").show();
            }
        }
    });

    $('#jq-datatables-example_wrapper .table-caption').text('Free Glass');
    $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
//        handleActionFooter();
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
