// all

var b_datatable_all = null;

init.push(function () {
    b_datatable_all = $('#jq-datatables-example-all').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        "paging": true,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        ajax: $.fn.dataTable.pipeline({
            "url": url_getwinemakers_items_all_ajax,
            "type" : "POST",
            "data": function (d) {
                d.wm_type = wm_type;
            }
        }),
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        "bAutoWidth" : false,
        "order": [[ 2, "desc" ]],
        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
            { "data" : "expert_img_html" },

            { "data" : "name" },
            { "data" : "domain" },

            { "data" : "address" },
            { "data" : "zip_code" },
            { "data" : "city" },
            { "data" : "country" },
            { "data" : "region" },

            { "data" : "phone_number" },
            { "data" : "website_url_link", orderable: false },
            { "data" : "status_html", orderable: true },
            { "data" : "social_links", orderable: false },
        ],

        drawCallback: function(settings) {

            $('[data-toggle="tooltip"]').tooltip();
    
            $('[name="ids"]').click(function() {
                handleActionFooter();
            });

            $("#jq-datatables-example-all_wrapper img:visible").unveil();

            var total_records = settings._iRecordsTotal;
            var search_value = $('#jq-datatables-example-all').DataTable().data().search();
           

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example-all_wrapper .table-caption').html('List of winemakers - '
                    + search_value + " : " + total_records);
            }else{
                $('#jq-datatables-example-all_wrapper .table-caption').text('List of winemakers : ' +
                    total_records);
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
    
    
    $('#jq-datatables-example-all_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-example-all-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-example-all-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_all.search('').draw(true);
    });  


    $('#toggle-all').click(function() {
        $('.table-bordered input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $("#ui-bootbox-publish").unbind("click");
    $("#ui-bootbox-unpublish").unbind("click");
    $("#ui-bootbox-indoubt").unbind("click");
    $("#ui-bootbox-bioorg").unbind("click");

    $("#ui-bootbox-delete").unbind("click");
    $("#ui-bootbox-duplicate").unbind("click");
    $("#ui-bootbox-cancel").unbind("click");
    $("#ui-bootbox-change-status-cancel").unbind("click");

    $("#ui-bootbox-publish").click(function(){
        statusConfirmation(url_winemakers_publish_ajax, 'winemakers', 'Publish');
    });

    $("#ui-bootbox-unpublish").click(function(){
        statusConfirmation(url_winemakers_unpublish_ajax, 'winemakers', 'Unpublish');
    });

    $("#ui-bootbox-indoubt").click(function(){
        statusConfirmation(url_winemakers_set_in_doubt_ajax, 'winemakers', 'In Doubt');
    });

    $("#ui-bootbox-bioorg").click(function(){
        statusConfirmation(url_winemakers_set_bio_organic_ajax, 'winemakers', 'Bio-Organic');
    });

    $("#ui-bootbox-investigate").click(function(){
        statusConfirmation(url_winemakers_set_to_investigate_ajax, 'winemakers', 'To Investigate');
        return false;
    });

    $("#ui-bootbox-delete").click(function(){
        massOperationConfirmPipeline(url_winemakers_delete_ajax,
                'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', 'winemakers');
    });

    $("#ui-bootbox-duplicate").click(function(){
        statusConfirmation(url_winemakers_duplicate_ajax, 'winemakers', 'Duplicate');
    });

    $("#ui-bootbox-cancel").click(function(){
        cancelSelection();
    });

    $("#ui-bootbox-change-status-cancel").click(function(){
        cancelSelection();
    })

});

// naturals

var b_datatable_naturals = null;

init.push(function () {
    b_datatable_naturals = $('#jq-datatables-example-naturals').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        "paging": true,
        ajax: $.fn.dataTable.pipeline({
            "url": url_getwinemakers_items_naturals_ajax,
            "type" : "POST",
            "data": function (d) {
                d.wm_type = wm_type;
            }
        }),

        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        'bAutoWidth' : false,

        "order": [[ 2, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
            { "data" : "expert_img_html" },

            { "data" : "name" },
            { "data" : "domain" },

            { "data" : "address" },
            { "data" : "zip_code" },
            { "data" : "city" },
            { "data" : "country" },
            { "data" : "region" },

            { "data" : "phone_number" },
            { "data" : "website_url_link", orderable: false },
            { "data" : "status_html", orderable: true },
            { "data" : "social_links", orderable: false },
        ],
        drawCallback: function(settings) {

            $('[data-toggle="tooltip"]').tooltip();
    
            $('[name="ids"]').click(function() {
                handleActionFooter();
            });

            $("#jq-datatables-example-naturals_wrapper img:visible").unveil();

            var total_records = settings._iRecordsTotal;
            var search_value = $('#jq-datatables-example-naturals').DataTable().data().search();
           

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example-naturals_wrapper .table-caption').html('List of winemakers - '
                    + search_value + " : " + total_records);
            }else{
                $('#jq-datatables-example-naturals_wrapper .table-caption').text('List of winemakers : ' +
                    total_records);
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
        b_datatable_naturals.search(search).draw(true);        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-example-naturals_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-example-naturals-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-example-naturals-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_naturals.search('').draw(true);
    });  

});

// others

var b_datatable_others = null;

init.push(function () {
    b_datatable_others = $('#jq-datatables-example-others').DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        "language": {
            "processing": '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>',
            "lengthMenu": "Per page: _MENU_",
        },
        dom: "<'row d-flex items-center m-0'<'col-sm-6'<'table-caption text-left'>><'col-sm-6 d-flex justify-end items-center'l<'positionFilter'>>>" +
        "<'row'<'col-sm-12'tr>>" +
        "<'row d-flex items-center m-0'<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>",
        "paging": true,
        ajax: $.fn.dataTable.pipeline({
            "url": url_getwinemakers_items_others_ajax,
            "type" : "POST",
            "data": function (d) {
                d.wm_type = wm_type;
            }
        }),

        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        'bAutoWidth' : false,

        "order": [[ 2, "desc" ]],

        columns: [
            { "data" : "checkbox_id", orderable: false },
            { "data" : "img_html", orderable: false },
            { "data" : "date" },
            { "data" : "author_img_html" },
            { "data" : "expert_img_html" },

            { "data" : "name" },
            { "data" : "domain" },

            { "data" : "address" },
            { "data" : "zip_code" },
            { "data" : "city" },
            { "data" : "country" },
            { "data" : "region" },

            { "data" : "phone_number" },
            { "data" : "website_url_link", orderable: false },
            { "data" : "status_html", orderable: true },
            { "data" : "social_links", orderable: false },
        ],
        drawCallback: function(settings) {

            $('[data-toggle="tooltip"]').tooltip();
    
            $('[name="ids"]').click(function() {
                handleActionFooter();
            });

            $("#jq-datatables-example-others_wrapper img:visible").unveil();

            var total_records = settings._iRecordsTotal;
            var search_value = $('#jq-datatables-example-others').DataTable().data().search();
           

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-example-others_wrapper .table-caption').html('List of winemakers - '
                    + search_value + " : " + total_records);
            }else{
                $('#jq-datatables-example-others_wrapper .table-caption').text('List of winemakers : ' +
                    total_records);
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
        b_datatable_others.search(search).draw(true);        
    }
    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-example-others_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-example-others-search"><i class="clear-search">x</i>')
    
    
    $(document).on('keyup', '#jq-datatables-example-others-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_others.search('').draw(true);
    }); 

});

    