function do_mop_wineposts(massOperationFunction) {
    var is_parent_post = $("#mop_parent_post").prop('checked')? true: false;
    var new_winemaker_id = $("#mop_jq-validation-select2").val();
    var new_parent_post_id = $("#mop_jq-validation-select2-multi").val();
    console.log(new_winemaker_id)
    if ($("#mop_define_as_child").prop('checked')){
        if (!new_parent_post_id || !new_winemaker_id){
            $("#mop_select2-jq-validation-select2-container").css('border', '1px solid red');
            alert("In order to define as children, please select new winemaker and wine");
            return false;
        }
    }
    massOperationFunction(
        url_mop_change_parent_post,
        'wineposts',
        [
            {'name': 'new_parent_post_id', 'value': new_parent_post_id},
            {'name': 'nat_oth',            'value': $("[name='nat_oth']:checked").val()},
            {'name': 'is_parent_post',     'value': is_parent_post},
            {'name': 'is_star_review',     'value': $("#mop_star_review").prop('checked')? true: false},
            {'name': 'define_as_child',    'value': $("#mop_define_as_child").prop('checked')? true: false}
        ]
    );
    $("#mop_define_as_child").prop('checked', false);
    $("#mop_parent_post").prop('checked', false);
    $("#mop_star_review").prop('checked', false);
    return false;
}


function mop_init(massOperationFunction) {
    if(massOperationFunction == undefined || massOperationFunction == null) {
        massOperationFunction = massOperationPipeline;
    }

    $("[name='nat_oth']").unbind('click');
    $("#mop_define_as_child").unbind('click');
    $("#mop_ui-bootbox-change-parent-cancel").unbind('click');
    $("#mop_ui-bootbox-change-parent-confirm").unbind('click');
//    $("#ui-bootbox-mop-update").unbind('click');
    $("#ui-bootbox-not-wine").unbind('click');

    $("[name='nat_oth']").click(function(){
        var which = $("[name='nat_oth']:checked").val();
        if(which == 'natural') {
            sel_display_natural = true;
            $(".display-natural").show();
            $(".display-other").hide();
        } else {
            sel_display_natural = false;
            $(".display-natural").hide();
            $(".display-other").show();
        }
    });

    $("#mop_ui-bootbox-change-parent-cancel").click(function(){
        //$("#mop_actionpostparent").hide();
        $("#mop_define_as_child").prop('checked', false);
    });

    $("#mop_ui-bootbox-change-parent-confirm").click(function(){
        do_mop_wineposts(massOperationFunction);
    });


    $("#ui-bootbox-mop-not-wine").click(function() {
        massOperationFunction(
            url_mop_move_to_general_post,
            'wineposts',
            [
            ]
        );
        return false;

    });

    var select_wine = $('#mop_jq-validation-select2-multi').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Wine...'
    }).change(function(){
        $("#mop_select2-jq-validation-select2-multi-container").css('border', 'none');
    });

    var select_wm = $('#mop_jq-validation-select2').select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Winemaker + Domain...',
        ajax: {
            url: url_mop_change_parent_post_winemaker_list,
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
                //if (id !== "") {
                //    $.ajax("/Customer/jsonLoadSelect2/" + id, {
                //        dataType: "json"
                //    }).done(function (data) { callback({ 'id': id, 'text': $('#uniqueCode').val() }) });
                //}
            },
            cache: true,
        }
    });

    select_wm.change(function(){
        var val = $(this).val();
        var is_parent_post = $("#mop_parent_post").prop('checked')? true: false;
        if (val && !is_parent_post) {
            $.ajax({
                type: "POST",
                dataType: "json",
                url: url_mop_change_parent_post_wine_list,
                data: {
                    "winemaker_id": val
                },
                success: function(data) {
                    $('#mop_jq-validation-select2-multi').empty();

                    if (data.items) {
                        select_wine = $('#mop_jq-validation-select2-multi').select2({
                            "data": data.items,
                            allowClear: true,
                            width: '100%',
                            placeholder: 'Select Wine...'
                        }).change(function(){
                            $("#mop_select2-jq-validation-select2-multi-container").css('border', 'none');
                        });
                    }
                },
                error: function(data){
                    console.warn(data);
                }
            });
        }else{
            $('#mop_jq-validation-select2-multi').empty();
        }
    });
}
