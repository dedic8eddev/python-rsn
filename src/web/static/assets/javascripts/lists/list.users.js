var b_datatable = null;

    init.push(function () {
        b_datatable = $('#jq-datatables-example').DataTable({
            "processing": true,
            "serverSide": true,
            "searchDelay": 1000,
            oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
            "paging": true,

            //ajax: {
            //   "url": url_get_user_items_ajax,
            //   "type" : "POST",
            //},

            ajax: $.fn.dataTable.pipeline({
                "url": url_get_user_items_ajax,
                "type" : "POST",
                // "data": function (d) {
                //    d.extra_search = $('#extra').val();
                // },
                
            }),

            "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
            "iDisplayLength": 50,
            'bAutoWidth' : false,

            "order": [[ 6, "desc" ]],

            columns: [
                { "data" : "checkbox_id", orderable: false },
                { "data" : "img_html" },
                { "data" : "full_name" },
                { "data" : "email" },

                { "data" : "post_number" },
                { "data" : "star_review_number" },
                { "data" : "account_created" },
                { "data" : "type_text" },

                { "data" : "lang", className: "user_language" },
                { "data" : "actions", orderable: false },
            ],
            drawCallback: function(settings) {

                
                $("td.user_language:empty").text( "Not recognized" );

                $('[data-toggle="tooltip"]').tooltip();

                $('[name="ids"]').unbind('click');

                $('[name="ids"]').click(function() {
                    $("#banuser").hide();
                    handleActionFooter();
                });

                $('[id^="ban_user_"]').unbind('click');

                $('[id^="ban_user_"]').click(function(){
                    $("#action").hide();
                    var id = $(this).attr('id').substr(9);
                    var url = url_users_ban_ajax;
                    var actionPanelId = "banuser";
                    var confirmButtonId = "ui-bootbox-ban-one";
                    var cancelButtonId = "ui-bootbox-cancel-one";
                    var entities = "users";
                    singleOperationConfirm(id, url, actionPanelId, confirmButtonId, cancelButtonId, entities)
                    return false;
                });

                $("#jq-datatables-example img:visible").unveil();

                var total_records = settings._iRecordsTotal;
                var search_value = b_datatable.data().search();

                if (search_value != undefined && search_value != null && search_value != ""){
                    $('#jq-datatables-example_wrapper .table-caption').text('Latest published wineposts - ' +
                        search_value + " : " + total_records);
                }else{
                    $('#jq-datatables-example_wrapper .table-caption').text('Latest published wineposts : ' + total_records);
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
                    //$(".paginate_button.active").prop('disabled', true);
                }else{
                    $(".paginate_button").show();
                    //$(".paginate_button.previous").show();
                    //$(".paginate_button.next").show();
                    //$(".paginate_button.active").prop('disabled', false);
                }

            }
        });

        $('#jq-datatables-example_wrapper .table-caption').text('Users');
        $('#jq-datatables-example_wrapper .dataTables_filter input').attr('placeholder', 'Search...');

        $('#toggle-all').click(function() {
            $('.table-bordered input[type="checkbox"]:enabled').prop('checked', $(this).prop('checked'));
            $("#banuser").hide();
            handleActionFooter();
        });

        $("#ui-bootbox-ban").click(function(){
            massOperationPipeline(url_users_ban_ajax, 'users');
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

    init.push(function () {
        $('[data-toggle="tooltip"]').tooltip();
    });
