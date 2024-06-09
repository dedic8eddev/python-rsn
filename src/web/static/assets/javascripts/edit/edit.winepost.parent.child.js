function confirm_parent_post() {
    $("#modal_is_pp").modal("hide");
    $("#id_is_parent_post").prop('checked', true);
    $("#winepost_edit_form").submit();
}


function cancel_parent_post() {
    $("#modal_is_pp").modal("hide");
    $("#winepost_edit_form").submit();
}


function select_wm_winepost_init(){
    select_wm_winepost = $('#id_winemaker').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Winemaker + Domain...',

        ajax: {
            url: ajax_change_parent_post_winemaker_list,
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    page: params.page,
                    edited_post_id: winepost_id,
                };
            },
            processResults: function (data, params) {
                for (i in data.items){
                    var item0 = data.items[i];
                    all_winemakers_by_ids[item0.id] = item0;
                }
                params.page = params.page || 1;

                return {
                    results: $.map(data.items, function(item){
                        return {
                            text: item.name,
                            id: item.id,
                        };
                    }),

                    pagination: {
                        more: (params.page * 30 ) < data.total_count
                    }
                };
            },
//            initSelection: function(element, callback) {
//                var id = $(element).val();
//            },
            cache: true,
        }
    });

    select_wm_winepost.change(function(){
        var val = $(this).val();

        if ((val in all_winemakers_by_ids) && (all_winemakers_by_ids[val] != undefined ) &&
            (all_winemakers_by_ids[val] != null) &&
            (all_winemakers_by_ids[val].domain != undefined) &&
            (all_winemakers_by_ids[val].domain != null)) {
            var selected_domain = all_winemakers_by_ids[val].domain;
            var editable = all_winemakers_by_ids[val].editable;
            $("#id_domain").val(selected_domain);


            if($("#id_original_winemaker_name").length > 0){
                if(editable) {
                    $("#id_original_winemaker_name").val(all_winemakers_by_ids[val].name);
                    $("#id_original_winemaker_name").prop('disabled', false);

                    $("#btn_open_edit_winemaker").prop('disabled', false);
                    $("#btn_update_winemaker_name").prop('disabled', false);
                    $("#btn_cancel_edit_winemaker").prop('disabled', false);
                }else{
                    $("#id_original_winemaker_name").val('-- can not edit this winemaker --');
                    $("#id_original_winemaker_name").prop('disabled', true);

                    $("#btn_open_edit_winemaker").prop('disabled', false);
                    $("#btn_update_winemaker_name").prop('disabled', false);
                    $("#btn_cancel_edit_winemaker").prop('disabled', false);
                }
            }
        }else{
            $("#id_domain").val("");
        }
    });
}

init.push(function () {
    // ============================ WM/DEFINE AS CHILD SELECT FOR MAIN WINEPOST FORM ============================
    $(".select2-search__field").attr('style', "");

    // select DEFINE AS CHILD data: WM and WINE
    select_wine = $('#jq-validation-select2-multi_wine_main_wp').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Wine...'
    }).change(function(){
        $("#select2-jq-validation-select2-multi_wine_main_wp-container").css('border', 'none');
    });

    select_wm = $('#jq-validation-select2_wm_main_wp').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Winemaker + Domain...',

        ajax: {
            url: ajax_change_parent_post_winemaker_list,
            dataType: 'json',
            delay: 250,
            data: function (params) {
                return {
                    q: params.term,
                    page: params.page,
                };
            },
            processResults: function (data, params) {
                params.page = params.page || 1;
                return {
                    results: $.map(data.items, function(item){
                        return {
                            text: item.name,
                            id: item.id
                        };
                    }),
                    pagination: {
                        more: (params.page * 30 ) < data.total_count
                    }
                };
            },
            initSelection: function(element, callback) {
                var id = $(element).val();
//                if (id !== "") {
//                    $.ajax("/Customer/jsonLoadSelect2/" + id, {
//                        dataType: "json"
//                    }).done(function (data) { callback({ 'id': id, 'text': $('#uniqueCode').val() }) });
//                }
            },
            cache: true,
        }
    });

    // select WM in "Winemaker" field
    select_wm_winepost_init();
    select_wm.change(function(){
        var val = $(this).val();

        if(val){
            $.ajax({
                type: "POST",
                dataType: "json",
                url: ajax_change_parent_post_wine_list,
                data: {
                    "winemaker_id": val
                },
                success: function(data) {
                    $('#jq-validation-select2-multi_wine_main_wp').empty();

                    if (data.items) {
                        select_wine = $('#jq-validation-select2-multi_wine_main_wp').select2({
                            "data": data.items,
                            allowClear: true,
                            width: '100%',
                            placeholder: 'Select Wine...'
                        }).change(function(){
                            $("#select2-jq-validation-select2-multi_wine_main_wp-container").css('border', 'none');
                        });
                    }
                },
                error: function(data){
                    console.warn(data);
                }
            });
        }else{
            $('#jq-validation-select2-multi_wine_main_wp').empty();
        }
    });

    var winemaker_errors = $("#winemaker_errors").val();
    if(winemaker_errors == 1){
        $("[aria-labelledby='select2-id_winemaker-container']").css('border-color','red');
    }
    // ============================ /WM/DEFINE AS CHILD SELECT FOR MAIN WINEPOST FORM ============================
});


    $("#ui-bootbox-change-parent-cancel").click(function(){
        $("#actionpostparent").hide();
        $("#define_as_child").prop('checked', false);
    });

    $("#ui-bootbox-change-parent-confirm").click(function(){
        var new_parent_post_id = $("#jq-validation-select2-multi_wine_main_wp").val();
        var new_winemaker_id = $("#jq-validation-select2_wm_main_wp").val();

        if (new_parent_post_id){
            $("#actionpostparent").hide();
            $("#define_as_child").prop('checked', false);

            $.ajax({
                type: "POST",
                dataType: "json",
                url: ajax_change_parent_post,
                data: {
                    "ids": winepost_id,
                    "new_parent_post_id": new_parent_post_id,
                    "define_as_child": true
                },
                success: function(data) {
                    if (data.status != undefined && data.status != null && data.status == 'OK'){
                        location.href = url_this_winepost_edit;
                    }
                },
                error: function(data){
                    console.warn(data);
                }
            });

        }else{
            $("#select2-jq-validation-select2-multi_wine_main_wp-container").css('border', '1px solid red');
            if (!new_winemaker_id){
                $("#select2-jq-validation-select2_wm_main_wp-container").css('border', '1px solid red');
                alert("Please select new winemaker and wine");
            }else{
                alert("Please select new wine");
            }
        }

        return false;
    });

    window.PixelAdmin.start(init);

    init.push(function () {
        $('[data-toggle="tooltip"]').tooltip();
    });
