// reviews

var b_datatable_reviews = null;
    
init.push(function () {
    b_datatable_reviews =  $('#jq-datatables-places-reviews').DataTable( {
        ajax: {
            "url": "/api/reports/reviews/",
            "type" : "GET", 
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-reviews-search").val();
            },
            dataSrc: 'results',
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3, 4, 5, 6],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="review'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.comment.author.username+'" data-authorid="'+oData.comment.author.id+'" data-status="'+oData.comment.author.status+'" type="checkbox">');
                }
            },
            {
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {                    
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString());
                },
                name: 'created_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.author.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.author.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.comment.author.get_images.image_thumb + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.place.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.place.name+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.comment.place.get_main_image  + '" /></a>');
                }
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display + '<span class="reported"></span>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.comment.description);
                }
            }
        ],
        "drawCallback": function(settings) {
            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-reviews img:visible").unveil();

            var search_value = b_datatable_reviews.data().search();
            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-reviews').DataTable().data().search();
            $(".reviews_count").text(total_records)
            localStorage.setItem("reviews-count",settings.json.recordsTotal);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-reviews_wrapper .table-caption').html('All RED-FLAGGED REVIEWS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-reviews_wrapper .table-caption').html('All RED-FLAGGED REVIEWS : ' + total_records);
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
        b_datatable_reviews.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-reviews_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-reviews-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-reviews-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-reviews').click(function() {
        $('#jq-datatables-places-reviews input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_reviews.search('').draw(true);
    }); 
      
});

// comments

var b_datatable_comments = null;
    
init.push(function () {
    b_datatable_comments =  $('#jq-datatables-places-comments').DataTable( {
        ajax: {
            "url": "/api/reports/comments/",
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-comments-search").val();
            },
            dataSrc: 'results',
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

        order: [[1, 'asc']],
        columns: [
            {
                name: '',
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="review'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.comment.author.username+'" data-authorid="'+oData.comment.author.id+'" data-status="'+oData.comment.author.status+'" type="checkbox">');
                }
            },
            {
                name: 'created_date',
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString());
                }
            },
            {
                name: 'author',
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.author.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.author.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.comment.author.get_images.image_thumb + '" /></a>');
                }

            },
            {
                name: 'post',
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.post.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.post.title+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.comment.post.main_image_url  + '" /></a>');
                }
            },
            {
                name: 'reporter',
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            {
                name: 'comment',
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.comment.description + '<span class="reported"></span>');
                }
            },
            {
                name: 'report',
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display.join(", "));
                }
            },

        ],
        columnDefs: [{
            'targets': [0, 2, 3, 4, 5, 6],
            'orderable': false,
        }],
        "drawCallback": function(settings) {
            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-comments img:visible").unveil();

            var search_value = b_datatable_reviews.data().search();
            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-reviews').DataTable().data().search();
            
            $(".comments_count").text(total_records)
            localStorage.setItem("comments-count",settings.json.recordsTotal);

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-comments_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER POSTS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-comments_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER POSTS : ' + total_records);
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
        b_datatable_comments.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-comments_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-comments-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-comments-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-comments').click(function() {
        $('#jq-datatables-places-comments input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_comments.search('').draw(true);
    }); 
       
});


// events

var b_datatable_events = null;
    
init.push(function () {
    b_datatable_events =  $('#jq-datatables-places-events').DataTable( {
        ajax: {
            "url": "/api/reports/events/",
            "type" : "GET",
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-events-search").val();
            },
            dataSrc: 'results'
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3, 4, 5, 6],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="event'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.comment.author.username+'" data-authorid="'+oData.comment.author.id+'" data-status="'+oData.comment.author.status+'" type="checkbox">');
                }
            },
            {
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {             
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString()); 
                },
                name: 'created_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.author.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.author.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.comment.author.get_images.image_thumb + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.comment.cal_event.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.comment.cal_event.title+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.comment.cal_event.main_image_url  + '" /></a>');
                }
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.comment.description + '<span class="reported"></span>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display.join(", "));
                }
            }
        ],
        "drawCallback": function(settings) {

            $(".dataTables_processing").hide()

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-events img:visible").unveil();

            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-events').DataTable().data().search();
           
            $(".events_count").text(total_records)
            localStorage.setItem("events-count",settings.json.recordsTotal);
            

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-events_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER EVENTS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-events_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER EVENTS : ' + total_records);
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
        b_datatable_events.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-events_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-events-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-events-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-events').click(function() {
        $('#jq-datatables-places-events input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_events.search('').draw(true);
    });
    
});

// picture


var b_datatable_pictures = null;
    
init.push(function () {
    b_datatable_pictures =  $('#jq-datatables-places-pictures').DataTable( {
        ajax: {
            "url": "/api/reports/pictures/",
            "type" : "GET",
            dataSrc: 'results',
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-pictures-search").val();
            }
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3, 4, 5],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="picture'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.post.author.username+'" data-authorid="'+oData.post.author.id+'" data-status="'+oData.post.author.status+'" type="checkbox">');
                }
            },
            {
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {             
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString()); 
                },
                name: 'created_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.post.author.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.post.author.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.post.author.get_images.image_thumb + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.post.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.post.title+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.post.main_image_url  + '" /></a>');
                }
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            // {
            //     data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
            //         $(nTd).html(oData.comment.description + '<span class="reported"></span>');
            //     }
            // },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display.join(", "));
                }
            }
        ],
        "drawCallback": function(settings) {

            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-pictures img:visible").unveil();

            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-pictures').DataTable().data().search();
            
            $(".pictures_count").text(total_records)
            localStorage.setItem("pictures-count",settings.json.recordsTotal);
            

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-pictures_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER POSTS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-pictures_wrapper .table-caption').html('All RED-FLAGGED COMMENTS UNDER POSTS : ' + total_records);
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
        b_datatable_pictures.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-pictures_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-pictures-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-pictures-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-pictures').click(function() {
        $('#jq-datatables-places-pictures input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_pictures.search('').draw(true);
    });
});


// users


var b_datatable_users = null;
    
init.push(function () {
    b_datatable_users =  $('#jq-datatables-places-users').DataTable( {
        ajax: {
            "url": "/api/reports/users/",
            "type" : "GET",
            dataSrc: 'results',
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-users-search").val();
            }
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3, 4],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="user'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.report_user.username+'" data-authorid="'+oData.report_user.id+'" data-status="'+oData.report_user.status+'" type="checkbox">');
                }
            },
            {
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {             
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString()); 
                },
                name: 'created_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.report_user.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.report_user.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.report_user.get_images.image_thumb + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display.join(", "));
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html(oData.reports_count);
                },
                name: 'reports_count'
            }

            
        ],
        "drawCallback": function(settings) {

            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-users img:visible").unveil();

            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-users').DataTable().data().search();
            
            $(".users_count").text(total_records)
            localStorage.setItem("users-count",settings.json.recordsTotal);
            

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-users_wrapper .table-caption').html('All REPORTED USERS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-users_wrapper .table-caption').html('All REPORTED USERS : ' + total_records);
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
        b_datatable_users.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-users_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-users-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-users-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-users').click(function() {
        $('#jq-datatables-places-users input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_users.search('').draw(true);
    });
});


// venues


var b_datatable_venues = null;
    
init.push(function () {
    b_datatable_venues =  $('#jq-datatables-places-venues').DataTable( {
        ajax: {
            "url": "/api/reports/venues/",
            "type" : "GET",
            dataSrc: 'results',
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-venues-search").val();
            }
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3, 4],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="venue'+oData.id+'" name="ids" value="'+oData.id+'" type="checkbox">');
                }
            },
            {
                data: "created_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {             
                    $(nTd).html(new Date(oData.created_date).toDateString() + ' ' + new Date(oData.created_date).toLocaleTimeString()); 
                },
                name: 'created_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.place.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.place.name+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.place.get_main_image + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.reporter.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.reporter.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.reporter.get_images.image_thumb  + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).addClass("text-left")
                    $(nTd).html(oData.report_display.join(", "));
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html(oData.reports_count);
                },
                name: 'reports_count'
            }
        ],
        "drawCallback": function(settings) {

            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-venues img:visible").unveil();

            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-venues').DataTable().data().search();
            
            $(".venues_count").text(total_records)
            localStorage.setItem("venues-count",settings.json.recordsTotal);
            

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-venues_wrapper .table-caption').html('All REPORTED VENUES - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-venues_wrapper .table-caption').html('All REPORTED VENUES : ' + total_records);
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
        b_datatable_venues.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-venues_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-venues-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-venues-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-venues').click(function() {
        $('#jq-datatables-places-venues input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_venues.search('').draw(true);
    });
});


// blocked users


var b_datatable_blocked_users = null;
    
init.push(function () {
    b_datatable_blocked_users =  $('#jq-datatables-places-blocked-users').DataTable( {
        ajax: {
            "url": "/api/users/block/",
            "type" : "GET",
            dataSrc: 'results',
            "data": function (d) {
                d.search_value = $("#jq-datatables-places-blocked-users-search").val();
            }
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
        order: [[1, 'asc']],
        columnDefs: [{
            'targets': [0, 2, 3],
            'orderable': false,
        }],
        columns: [
            {
                data: "id", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<input id="blockedUser'+oData.id+'" name="ids" value="'+oData.id+'" data-author="'+oData.block_user.username+'" data-authorid="'+oData.block_user.id+'" data-status="'+oData.block_user.status+'" type="checkbox">');
                }
            },
            {
                data: "blocked_date", "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html(new Date(oData.blocked_date).toDateString() + ' ' + new Date(oData.blocked_date).toLocaleTimeString());
                },
                name: 'blocked_date'
            },
            {
                data: null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.block_user.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.block_user.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" class="rounded-img" src="' + oData.block_user.get_images.image_thumb + '" /></a>');
                }
            },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html('<a href="'+oData.user.absolute_url+'" class="dynamicTooltip" data-original-title="'+oData.user.username+'" data-toggle="tooltip" data-placement="top"><img width="35" height="35" src="' + oData.user.get_images.image_thumb  + '" /></a>');
                }
            },
            // {
            //     data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
            //         $(nTd).addClass("text-left")
            //         $(nTd).html(oData.report);
            //     }
            // },
            {
                data:null, "fnCreatedCell": function (nTd, sData, oData, iRow, iCol) {
                    $(nTd).html(oData.blocks_count);
                },
                name: "blocks_count"
            }
        ],
        "drawCallback": function(settings) {

            $(".dataTables_processing").hide();

            $('[data-toggle="tooltip"]').tooltip();

            $('[name="ids"]').click(function() {
                handleActionFooter();
            });
            $("#jq-datatables-places-blocked-users img:visible").unveil();

            var total_records =  settings._iRecordsTotal;
            var search_value = $('#jq-datatables-places-blocked-users').DataTable().data().search();
            
            $(".blocked-users_count").text(total_records)
            localStorage.setItem("venues-count",settings.json.recordsTotal);
            

            if (search_value != undefined && search_value != null && search_value != ""){
                $('#jq-datatables-places-blocked-users_wrapper .table-caption').html('All BLOCKED USERS - ' + search_value + " : " + total_records);

            }else{
                $('#jq-datatables-places-blocked-users_wrapper .table-caption').html('All BLOCKED USERS : ' + total_records);
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
        b_datatable_blocked_users.search(search).draw(true);        
    }

    const processChange = debounce((search) => saveInput(search));
    
    
    $('#jq-datatables-places-blocked-users_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="jq-datatables-places-blocked-users-search"><i class="clear-search">x</i>')
    
    $(document).on('keyup', '#jq-datatables-places-blocked-users-search', function() {
        var value = $(this).val();
        if(value.length > 0){
            $(this).parents(".positionFilter").addClass("searched")
        }else{
            $(this).parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });

    $('#toggle-all-venues').click(function() {
        $('#jq-datatables-places-blocked-users input[type="checkbox"]').prop('checked', $(this).prop('checked'));
        handleActionFooter();
    });

    $(document).on('click', '.clear-search', function() {
        $(this).siblings('input').val('');
        $(this).parents(".positionFilter").removeClass("searched")
        b_datatable_blocked_users.search('').draw(true);
    });
    
    localStorage.removeItem("activeTab");

    $('a[data-toggle="tab"]').on('shown.bs.tab', function (e) {
        localStorage.setItem("activeTab",$(this).attr("id"))
    })
    $("#ui-bootbox-delete").click(function(){

        var url = "/api/reports/";
        if(localStorage.getItem("activeTab")=="blockedUsers"){
            url = "/api/users/block/"
        }else{
            url = "/api/reports/"
        }

        massOperationConfirmPipelineDelete( url,
             'action_delete_confirm', 'ui-bootbox-delete-confirm', 'ui-bootbox-delete-cancel', '');

    });

    $("#ui-bootbox-unban-user").click(function(){
        massOperationPipelineBanUnban("/ajax/users/unban/", '','','unban');
    });


    $("#ui-bootbox-ban-user").click(function(){
        massOperationConfirmPipelineBanUnban("/ajax/users/ban/",
            'action_ban_user_confirm', 'ui-bootbox-ban-user-confirm', 'ui-bootbox-ban-user-cancel', '','ban');
    });

    $("#ui-bootbox-cancel").click(function(){
        cancelSelection();
    });
        
    $(".all_count").html(parseInt(localStorage.getItem("reviews-count")) + parseInt(localStorage.getItem("comments-count")) + parseInt(localStorage.getItem("events-count")) + parseInt(localStorage.getItem("pictures-count")))
});