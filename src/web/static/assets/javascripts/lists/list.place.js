// all

var b_datatable_all = null;
    
init.push(function () {
    b_datatable_all =  $('#jq-datatables-places-all').DataTable( {
        ajax: {
            "url": url_get_place_items_ajax_all,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-all-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "ordering": true,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-all img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-all').DataTable().data().search();
               
               $('.all_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-all_wrapper .table-caption').html('All - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-all_wrapper .table-caption').html('All : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
    });

    $("#ui-bootbox-delete").click(function(){
        massOperationConfirmPipeline(url_places_delete_ajax,
            'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', 'places');
    });

    $("#ui-bootbox-duplicate").click(function(){
        massOperationPipeline(url_places_duplicate_ajax, 'places');
    });

    $("#ui-bootbox-change-status-cancel").click(function(){
        cancelSelection();
    })

    $("#ui-bootbox-cancel").click(function(){
        cancelSelection();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_all.search('').draw(true);
    });    
});

// free

var b_datatable_free = null;
    
init.push(function () {
    b_datatable_free =  $('#jq-datatables-places-free').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_free,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-free-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-free img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-free').DataTable().data().search();
               
                $('.free_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-free_wrapper .table-caption').html('Free - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-free_wrapper .table-caption').html('Free : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_free.search('').draw(true);
    });    
});

// trial

var b_datatable_in_trial = null;
    
init.push(function () {
    b_datatable_in_trial =  $('#jq-datatables-places-in-trial').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_in_trial,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-in-trial-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-in-trial img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-in-trial').DataTable().data().search();
               
                $('.in_trial_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-in-trial_wrapper .table-caption').html('In Trial - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-in-trial_wrapper .table-caption').html('In Trial : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_in_trial.search('').draw(true);
    });    
});

// subscribers

var b_datatable_subscribers = null;
    
init.push(function () {
    b_datatable_subscribers =  $('#jq-datatables-places-subscribers').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_subscribers,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-subscribers-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-subscribers img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-subscribers').DataTable().data().search();
               
                $('.subscribers_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-subscribers_wrapper .table-caption').html('Subscribers - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-subscribers_wrapper .table-caption').html('Subscribers : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_subscribers.search('').draw(true);
    });    
});

// not_connected

var b_datatable_not_connected = null;

init.push(function () {
    b_datatable_not_connected =  $('#jq-datatables-places-not-connected').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_not_connected,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-not-connected-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        "bAutoWidth" : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "pageLength"  :10,
        "order": [],
        columns: [
            { "data" : "checkbox_id" , orderable: false},
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
            { "data" : "expert_img_html"},

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
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-not-connected img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-not-connected').DataTable().data().search();
               
                $('.not_connected_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-not-connected_wrapper .table-caption').html('Not Connected - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-not-connected_wrapper .table-caption').html('Not Connected : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_not_connected.search('').draw(true);
    });    
});

// stickers

var b_datatable_stickers = null;

init.push(function () {
    b_datatable_stickers =  $('#jq-datatables-places-stickers').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_stickers,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-stickers-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-stickers img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-stickers').DataTable().data().search();
               
                $('.stickers_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-stickers_wrapper .table-caption').html('Stickers - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-stickers_wrapper .table-caption').html('Stickers : ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_stickers.search('').draw(true);
    });    
});

// stickers_to_send

var b_datatable_stickers_to_send = null;

init.push(function () {
    b_datatable_stickers_to_send =  $('#jq-datatables-places-stickers-to-send').DataTable({
        ajax: {
            "url": url_get_place_items_ajax_stickers_to_send,
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-stickers-to-send-search").val();
            },
        },
        "processing": true,
        "searchDelay": 1000,
        "serverSide": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
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
            { "data" : "chargebee_status" },
            { "data" : "trial_ends"},
            { "data" : "src"},
            { "data" : "owner"},
            { "data" : "info"}
        ],
        "drawCallback": function(settings) {
                $('[data-toggle="tooltip"]').tooltip();
    
                $('[name="ids"]').click(function() {
                    handleActionFooter();
                });
                $("#jq-datatables-places-stickers-to-send img:visible").unveil();
    
                var total_records = settings._iRecordsTotal;
                var search_value = $('#jq-datatables-places-stickers-to-send').DataTable().data().search();
               
                $('.stickers_to_send_count').text(settings.json.recordsTotal);
    
                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-places-stickers-to-send_wrapper .table-caption').html('Stickers to send - '
                        + search_value + " : " + total_records  +
                            ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                            ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
    
                }else{
                    $('#jq-datatables-places-stickers-to-send_wrapper .table-caption').html('Stickers to send: ' + total_records +
                        ' -  <a class="caption-est-comments" href="' + url_comments + '">comments</a>' +
                        ' -  <a class="caption-est-comments" href="' + url_free_glass + '">Free Glass</a>');
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
        b_datatable_stickers.search(search).draw(true);        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-stickers-to-send_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-stickers-to-send-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-places-stickers-to-send-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_places_publish_ajax, 'places', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_places_unpublish_ajax, 'places', 'Draft');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_places_set_in_doubt_ajax, 'places', 'In Doubt');
    });

    $("#ui-bootbox-close").click(function(){
        statusConfirmation(url_places_close_ajax, 'places', 'Close');
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

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_stickers_to_send.search('').draw(true);
    });    
});

