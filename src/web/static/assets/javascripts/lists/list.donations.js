var b_datatable = null;

init.push(function () {
    b_datatable = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        ajax: $.fn.dataTable.pipeline({
            "url": url_donation_items_ajax,
            "type" : "POST",
            "data": function (d) {
                d.extra_search = $('#extra').val();
            }
        }),
        'bAutoWidth' : false,

        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

        "order": [[ 2, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "author_img_html", orderable: true },
            { "data" : "author_email", orderable: true },
            { "data" : "modified_time", orderable: true },

            { "data" : "value_data" },
            { "data" : "frequency", orderable: false },
            { "data" : "date_from", orderable: true },

            { "data" : "date_to", orderable: true },
            { "data" : "total_amounts", orderable: false },
        ],

        drawCallback: function(settings) {
            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });

            $("#jq-datatables-example img:visible").unveil();

            // var total_records = b_datatable.fnSettings().fnRecordsTotal();
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable.data().search();

            var url_free_glass = "";
            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example_wrapper .table-caption').html('LATEST DONATIONS : ' + search_value +
                    ":" + total_records);
            }else{
                $('#jq-datatables-example_wrapper .table-caption').html('LATEST DONATIONS : ' + total_records);
            }

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

    $('#jq-datatables-example_wrapper .table-caption').text('Latest donations');
    $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
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
