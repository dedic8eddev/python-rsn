var b_datatable = null;

init.push(function () {
    b_datatable = $('#jq-datatables-example').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        "paging": true,

        ajax: $.fn.dataTable.pipeline({
            "url": url_items_ajax,
            "type" : "POST",
            //"data": function (d) {
            //    d.extra_search = $('#extra').val();
            //}
        }),


        'bAutoWidth' : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],

        "order": [[ 2, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "lpb_img_html", orderable: false },
            { "data" : "date", orderable: true },
            { "data" : "author_img_html", orderable: false },
            { "data" : "title", orderable: true },
            { "data" : "status_en", orderable: false},
            { "data" : "status_fr", orderable: false},
            { "data" : "status_ja", orderable: false},
            { "data" : "status_it", orderable: false},
            { "data" : "status_es", orderable: false},
            
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

           $('#jq-datatables-example_wrapper .table-caption').html('La Petite Boucle: ' + total_records);

            if (search_value != undefined && search_value != null && search_value != "") {
                $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            } else {
                $('.clear-search').remove();
            }

            var paginate_button_count = $(".paginate_button").not(".paginate_button.previous").
                not(".paginate_button.next").length;
            if (paginate_button_count < 2){
                $(".paginate_button").hide();
            }else{
                $(".paginate_button").show();
            }
        }
    });

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish-confirm").click(function(){
        massOperationPipeline(url_lpb_publish_ajax, 'posts');
    });
    $("#ui-bootbox-publish").click(function(){
        $("#action_publish_confirm").css('display', 'block');
        $("#action_main").css('display', 'none');
    });
    $("#ui-bootbox-merge-confirm").click(function(){
        massOperationPipeline(url_lpb_merge_ajax, 'posts');
    });
    $("#ui-bootbox-merge").click(function(){
        $("#action_merge_confirm").css('display', 'block');
        $("#action_main").css('display', 'none');
    });
    $("#ui-bootbox-unpublish-confirm").click(function(){
        massOperationPipeline(url_lpb_unpublish_ajax, 'posts');
    });
    $("#ui-bootbox-unpublish").click(function(){
        $("#action_unpublish_confirm").css('display', 'block');
        $("#action_main").css('display', 'none');
    }); 

    $("#ui-bootbox-delete").click(function(){
        $("#action_delete_confirm").css('display', 'block');
        $("#action_main").css('display', 'none');
    });
    $("#ui-bootbox-delete-confirm").click(function(){
        massOperationPipeline(url_lpb_delete_ajax, 'posts');
    });
    $("#ui-bootbox-cancel, #ui-bootbox-delete-cancel, #ui-bootbox-publish-cancel, #ui-bootbox-merge-cancel, #ui-bootbox-unpublish-cancel").click(function(){
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
