var b_datatable = null;

    init.push(function () {
        b_datatable = $('#jq-datatables-example').DataTable({
            "processing": true,
            "serverSide": true,
            "searchDelay": 1000,
            oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
            "paging": true,

//            ajax: {
//                "url": url_general_post_items_ajax,
//                "type" : "POST",
//            },

            ajax: $.fn.dataTable.pipeline({
                "url": url_general_post_items_ajax,
                "type" : "POST",
//                "data": function (d) {
//                    d.extra_search = $('#extra').val();
//                }
            }),

            'bAutoWidth' : false,
            "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

            "order": [[ 2, "desc" ]],

            columns: [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html", orderable: false },
                { "data" : "date" },
                { "data" : "author_img_html", orderable: true },

                { "data" : "title" },
                { "data" : "description" },
                { "data" : "status_html" },
                { "data" : "place_html", orderable: false },
                { "data" : "comment_number" },
                { "data" : "likevote_number" },
            ],
            drawCallback: function(settings) {
                $('[data-toggle="tooltip"]').tooltip();

                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });

                $("#jq-datatables-example img:visible").unveil();

//                var total_records = b_datatable.dataTable().fnSettings().fnRecordsTotal();
                var total_records = settings._iRecordsTotal;
                var search_value = b_datatable.data().search();

                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-example_wrapper .table-caption').text('User’s posts (not wine) - ' +
                        search_value + " : " + total_records);
                }else{
                    $('#jq-datatables-example_wrapper .table-caption').text('User’s posts (not wine): ' + total_records);
                }

                if (search_value != undefined && search_value != null && search_value != "") {
                    $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
                } else {
                    $('.clear-search').remove();
                }

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
                }            }
        });

        $('#jq-datatables-example_wrapper .table-caption').text('User’s posts (not wine):');
        $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

        $('#toggle-all').click(function() {
            $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
            handleActionFooter();
        });

        $("#ui-bootbox-publish").click(function(){
            massOperationPipeline(url_generalposts_publish_ajax, 'posts');
        });

        $("#ui-bootbox-unpublish").click(function(){
            massOperationPipeline(url_generalposts_unpublish_ajax, 'posts');
        });

        $("#ui-bootbox-delete").click(function(){
            massOperationConfirmPipeline(url_generalposts_refuse_ajax,
                 'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', 'posts');
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
