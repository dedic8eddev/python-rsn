// all

var b_datatable_all = null;

init.push(function () {
    b_datatable_all = $('#jq-datatables-places-all').DataTable({
        "processing": true,
           "bServerSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",

       // ajax:url_get_place_items_ajax_all,
        "fnServerData": function (source, data, callback) {
            $.ajax({
                "dataType": 'json',
                "contentType": "application/json; charset=utf-8",
                "type": "GET",
                "url": url_get_place_items_ajax_all,
                "data": data,
                "success": function (response) {
                    var json = jQuery.parseJSON(response.d);
                    callback(json);
                }
            });
        },


        
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_all,
        //     "type" : "POST",
        //     "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),
 
        
        "bAutoWidth" : false,
        "paging": true,
        "searching": true,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,

        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
            // ,
            // { "data" : "social_links", orderable: false },
            // { "data" : "sticker" }
        ],
        drawCallback: function(settings) {



            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-all img:visible").unveil();

            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_all.data().search();

            $('.all_count').text(total_records);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-all_wrapper .table-caption').html('All - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-all_wrapper .table-caption').html('All : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        b_datatable_all.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-all_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-all-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-all-search', function() {
        var value = $(this).val();

        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }

        processChange(value);
    });



    $('#jq-datatables-places-all_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_all.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_all.draw(true);
    //     }, 500 );
    //   }
    //   });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_all.search('').draw(true);
    });
        
});

// free

var b_datatable_free = null;

init.push(function () {
    b_datatable_free = $('#jq-datatables-places-free').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},     
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        ajax:url_get_place_items_ajax_free,
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_free,
        //     "type" : "POST",
        //     "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),


        
        bAutoWidth : false,
        paging: true,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,

        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
            // ,
            // { "data" : "social_links", orderable: false },
            // { "data" : "sticker" }
        ],
        drawCallback: function(settings) {



            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-free img:visible").unveil();

            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_free.data().search();

            $('.free_count').text(total_records);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-free_wrapper .table-caption').html('Free - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-free_wrapper .table-caption').html('Free : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        b_datatable_free.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-free_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-free-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-free-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#jq-datatables-places-free_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_free.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_free.draw(true);
    //     }, 500 );
    //   }
    //   });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_free.search('').draw(true);
    });        
});

// in trial

var b_datatable_in_trial = null;

init.push(function () {
    b_datatable_in_trial = $('#jq-datatables-places-in-trial').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        ajax:url_get_place_items_ajax_in_trial,
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_in_trial,
        //     "type" : "POST",
        //     "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),

        bAutoWidth : false,
        paging: true,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,
        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
            // ,
            // { "data" : "social_links", orderable: false },
            // { "data" : "sticker" }
        ],
        drawCallback: function(settings) {



            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-in-trial img:visible").unveil();

            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_in_trial.data().search();

            $('.in_trial_count').text(total_records);


            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-in-trial_wrapper .table-caption').html('In Trial - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-in-trial_wrapper .table-caption').html('In Trial : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        b_datatable_in_trial.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-in-trial_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-in-trial-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-in-trial-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#jq-datatables-places-in-trial_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_in_trial.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_in_trial.draw(true);
    //     }, 500 );
    //   }
    //   });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_in_trial.search('').draw(true);
    });        
});

// subscribers

var b_datatable_subscribers = null;

init.push(function () {
    b_datatable_subscribers = $('#jq-datatables-places-subscribers').DataTable({
        "processing": true,
       // "serverSide": true,
        "searchDelay": 1000,
        "paging": true,
        bPaginate: true,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
       // ajax:url_get_place_items_ajax_subscribers,

       "ajax": {
            "url": "/ajax/place/items-opti/subscribers/",
            "type": "GET"
        },


        
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_subscribers,
        //     "type" : "GET",
        //     dataType: 'json',
        //     contentType: 'json',
        //    // "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),

        
        "bAutoWidth" : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,

        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
        ],
        drawCallback: function(settings) {

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-subscribers img:visible").unveil();

            //b_datatable_subscribers.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_subscribers.data().search();

            $('.subscribers_count').text(total_records);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-subscribers_wrapper .table-caption').html('Subscribers - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-subscribers_wrapper .table-caption').html('Subscribers : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        b_datatable_subscribers.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-subscribers_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-subscribers-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-subscribers-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });



    $('#jq-datatables-places-subscribers_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_subscribers.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_subscribers.draw(true);
    //     }, 500 );
    //   }
    // });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_subscribers.search('').draw(true);
    });        
});

// not connected

var b_datatable_not_connected = null;

init.push(function () {
    b_datatable_not_connected = $('#jq-datatables-places-not-connected').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        ajax:url_get_place_items_ajax_not_connected,
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_not_connected,
        //     "type" : "POST",
        //     "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),


        
        bAutoWidth : false,
        paging: true,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,

        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
            // ,
            // { "data" : "social_links", orderable: false },
            // { "data" : "sticker" }
        ],
        drawCallback: function(settings) {



            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-not-connected img:visible").unveil();

            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_not_connected.data().search();

            
            $('.not_connected_count').text(total_records);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-not-connected_wrapper .table-caption').html('Not Connected - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-not-connected_wrapper .table-caption').html('Not Connected : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        b_datatable_not_connected.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-not-connected_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-not-connected-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-not-connected-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });


    $('#jq-datatables-places-not-connected_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_not_connected.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_not_connected.draw(true);
    //     }, 500 );
    //   }
    //   });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_not_connected.search('').draw(true);
    });        
});

// stickers

var b_datatable_stickers = null;

init.push(function () {
    b_datatable_stickers = $('#jq-datatables-places-stickers').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        ajax:url_get_place_items_ajax_stickers,
        // ajax: $.fn.dataTable.pipeline({
        //     "url": url_get_place_items_ajax_stickers,
        //     "type" : "POST",
        //     "autoWidth": true
        //     // "data": function (d) {
        //     //     d.extra_search = $('#extra').val();
        //     // }
        // }),


        
        bAutoWidth : false,
        paging: true,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,

        "order": [],

        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
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
            { "data" : "chargebee_status" }
            // ,
            // { "data" : "social_links", orderable: false },
            // { "data" : "sticker" }
        ],
        drawCallback: function(settings) {



            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-stickers img:visible").unveil();

            // b_datatable.fnSettings().fnRecordsTotal()
            var total_records = settings._iRecordsTotal;
            var search_value = b_datatable_stickers.data().search();

            $('.stickers_count').text(total_records);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-stickers_wrapper .table-caption').html('Stickers - '
                    + search_value + " : " + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');

            }else{
                $('#jq-datatables-places-stickers_wrapper .table-caption').html('Stickers : ' + total_records +
                    ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                    ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
            }

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $(".form-control.input-sm[type='search']").parent().append('<i class="clear-search" id="clear-search">x</i>');
            // } else {
            //     $('.clear-search').remove();
            // }

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

    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        b_datatable_stickers.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-stickers_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-stickers-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-stickers-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });


    $('#jq-datatables-places-stickers_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

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

    // $(".form-control.input-sm[type='search']").unbind();

    // var keyPressTimeout;
    // $(".form-control.input-sm[type='search']").bind('keyup', function(e) {
    //   if (this.value.length > 2 || this.value.length === 0) {
    //     b_datatable_stickers.search(this.value);
    //     clearTimeout(keyPressTimeout);
    //     keyPressTimeout = setTimeout(function() {
    //           b_datatable_stickers.draw(true);
    //     }, 500 );
    //   }
    //   });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        b_datatable_stickers.search('').draw(true);
    });        
});


init.push(function () {
    $('[data-toggle="tooltip"]').tooltip();
});



