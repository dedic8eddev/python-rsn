function DataTableFactory(table_id, title_format_str, title_format_str_with_search,
        title_format_params, url, columns, default_order,
        mass_operations, action_panel_id, entities,searchId) {
    this.setTitleFormat(title_format_str, title_format_str_with_search, title_format_params);
    this.is_pipeline = true;        // ALWAYS VIA PIPELINE (maybe later we'll add the in-memory handling)
    this.datatable_element = null;  // DOM element for datatable
    this.table_id = table_id;
    this.url = url;
    this.columns = columns;
    this.default_order = default_order;
    this.mass_operations = mass_operations;
    this.postStatus = "Parent Post";
    this.action_panel_id = action_panel_id;
    this.entities = entities;
    this.searchId = searchId;
    this.statusAction = 'status';
    this.statusText = '.action_new_status';
    // paths
    this.tooltip_path = '[data-toggle="tooltip"]';
    this.table_path = "#" + this.table_id;
    this.toggle_all_element_path = "#" + this.table_id + ' .toggle-all';
    this.all_row_ids_path = '#' + this.table_id + ' [name="ids"]';
    this.all_checked_row_ids_path = '#' + this.table_id + ' [name="ids"]:checked';
    this.all_checkboxes_path = "#" + this.table_id + ' input[type="checkbox"]';
    this.action_panel_path = '#' + this.action_panel_id;
    this.action_cancel_selection_path = "#" + action_panel_id + " .do-cancel";
    this.action_item_number_path = "#" + this.action_panel_id + "  .action_item_number";
    this.action_confirm_path = "#" + this.action_panel_id + "  .action-confirm";
    this.action_main_path = "#" + this.action_panel_id + " .action-main";
    this.visible_images_path = "#" + this.table_id + " img:visible";
    this.table_caption_path = "#" + this.table_id + '_wrapper .table-caption';
    this.paginate_button_path = "#" + this.table_id +" .paginate_button";
    this.paginate_button_previous_path = "#" + this.table_id +" .paginate_button.previous";
    this.paginate_button_next_path = "#" + this.table_id +" .paginate_button.next";
    this.filter_input_path = "#" + this.table_id + '_wrapper .dataTables_filter input';

}


DataTableFactory.prototype.getMenuNumPath = function(entities) {
    return "#menu_num_" + entities;
}


DataTableFactory.prototype.handleActionFooter = function() {
    if($(this.all_checked_row_ids_path).length > 0){
        const htmlText = $(this.all_checked_row_ids_path).length === 1 ? ($(this.all_checked_row_ids_path).length + " " + "Entry") : ($(this.all_checked_row_ids_path).length + " " + "Entries");
        $(this.action_item_number_path).html("" + htmlText);
        $(this.statusText).html(this.statusAction);
        $(this.action_confirm_path).hide();
        $(this.action_panel_path).show();
        $(this.action_main_path).show();
        $(this.mop_define_as_child_path).prop('checked', false);
        $(this.mop_parent_post_path).prop('checked', false);
        $(this.mop_star_review_path).prop('checked', false); 
        $(this.nat_oth_path).prop('checked', false);
        this.show_pro_selector_wm();
        this.show_pro_selector_wine();
        $(this.pro_selector_wine_status_path).hide();
       // $(this.wm_selector_path).val(null).trigger('change');
       // $(this.wine_selector_path).val(null).trigger('change');

        

        var selectedWinemaker = $(this.wm_selector_path)

        if (window.location.href.indexOf("wineposts") > -1) {
           
            var lastModeratedWineId = localStorage.getItem("lastModeratedWineId")
            var lastModeratedWineName = localStorage.getItem("lastModeratedWineName");
            if(lastModeratedWineId && lastModeratedWineName){
                var option = new Option(lastModeratedWineName, lastModeratedWineId, true, true);
                selectedWinemaker.append(option).trigger('change');
            }
            else{
                selectedWinemaker.val(null).trigger('change');
            }
        }else{
            $.ajax({
                type: 'GET',
                url: url_change_parent_post_list_winemaker_ajax 
            }).then(function (data) {
                console.log(data.items[0].name)
                var option = new Option(data.items[0].name, data.items[0].id, true, true);
                selectedWinemaker.append(option).trigger('change');
                selectedWinemaker.trigger({
                    type: 'select2:select',
                    params: {
                        data: data
                    }
                });
            });    
        }
           


    }else{
        $(this.action_panel_path).hide();
        $(this.toggle_all_element_path).prop('checked', false);
    }
}


DataTableFactory.prototype.cancelSelection = function() {
    $(this.toggle_all_element_path).prop('checked', false);
    if($(this.all_checked_row_ids_path).length > 0){
        $(this.all_checked_row_ids_path).prop('checked', false);
    }
    $(this.action_panel_path).hide();
}


DataTableFactory.prototype.uncheck_mop_parent_post = function() {
    $(this.mop_parent_post_path).prop('checked', false);
}

DataTableFactory.prototype.uncheck_define_as_child = function() {
    $(this.mop_define_as_child_path).prop('checked', false);
}

DataTableFactory.prototype.uncheck_mop_star_review = function() {
    $(this.mop_star_review_path).prop('checked', false);
}

DataTableFactory.prototype.show_pro_selector_wm = function() {
    $(this.pro_selector_wm_path).show();
}

DataTableFactory.prototype.show_pro_selector_wine = function() {
    $(this.pro_selector_wine_path).show();
}

DataTableFactory.prototype.hide_pro_selector_wine = function() {
    $(this.pro_selector_wine_path).hide();
}

DataTableFactory.prototype.is_mop_parent_post_checked = function() {
    var checked = $(this.mop_parent_post_path).prop('checked')? true: false;
    return checked;
}

DataTableFactory.prototype.is_mop_star_review_checked = function() {
    var checked = $(this.mop_star_review_path).prop('checked')? true: false;
    return checked;
}

DataTableFactory.prototype.is_define_as_child_checked = function() {
    var checked = $(this.mop_define_as_child_path).prop('checked')? true: false;
    return checked;
}


DataTableFactory.prototype.refreshList = function() {
    if (this.is_pipeline) {
        $(this.table_path).DataTable().clearPipeline().draw(false);
    } else {
        $(this.table_path).DataTable().ajax.reload();
    }
}


DataTableFactory.prototype.setTitleFormat = function(title_format_str, title_format_str_with_search, title_format_params) {
    this.title_format_str = title_format_str;
    this.title_format_str_with_search = title_format_str_with_search;
    this.title_format_params = title_format_params;
}


DataTableFactory.prototype.getTitle = function() {
    if (this.title_format_params['search'] != undefined &&
            this.title_format_params['search'] != null &&
            this.title_format_params['search'] != '') {
        var title_format_str = this.title_format_str_with_search;
    } else {
        var title_format_str = this.title_format_str;
    }

    title_out = title_format_str;
    for (param in this.title_format_params) {
        var param_val = this.title_format_params[param];
        title_out = title_out.replace('{' + param + '}', param_val);
    }
    return title_out;
}


DataTableFactory.prototype.setTitle = function() {
    $(this.table_caption_path).text(this.getTitle());
}


// TODO: in the later version I want to make this DataTableFactory independent from wineposts, but for now,
// TODO: do_mop_wineposts which executes changing of the parent post will be setup here
DataTableFactory.prototype.do_mop_wineposts = function() {
    var new_winemaker_id = $(this.wm_selector_path).val();
    var new_parent_post_id = $(this.wine_selector_path).val();
    var wine_status = $(this.pro_selector_wine_status_path).find('select').val();
    
    var new_winemaker_name = $(this.wm_selector_path).find("option:last").text();
    localStorage.setItem("lastModeratedWineId",new_winemaker_id);
    localStorage.setItem("lastModeratedWineName",new_winemaker_name);

    console.log("selected " + wine_status)

    if (this.is_define_as_child_checked()) {
        if (!new_parent_post_id || !new_winemaker_id) {
            $(this.wm_selector_container_path).css('border', '1px solid red');
            alert("In order to define as children, please select new winemaker and wine");
            return false;
        }
    } else if (this.is_mop_parent_post_checked()) {
        if (!new_winemaker_id){
            $(this.wm_selector_container_path).css('border', '1px solid red');
            alert("In order to create a new parent post, please select new winemaker");
            return false;
        }
    }

    var mop_ser_array = [
        {'name': 'new_parent_post_id', 'value': new_parent_post_id},
        {'name': 'new_winemaker_id', 'value': new_winemaker_id},
        {'name': 'status',    'value': wine_status},
        {'name': 'nat_oth',            'value': $(this.nat_oth_checked_path).val()},
        {'name': 'is_parent_post',     'value': this.is_mop_parent_post_checked()},
        {'name': 'is_star_review',     'value': this.is_mop_star_review_checked()},
        {'name': 'define_as_child',    'value': this.is_define_as_child_checked()}   
    ];

    if(this.is_mop_parent_post_checked()) {

        var serArray = $(this.all_checked_row_ids_path).serializeArray();
        var thys = this;
        $.ajax({
            type: "POST",
            url: url_mop_has_children,
            data: serArray,
            dataType: 'json',
            success: function(data) {
                if(data.has_children) {
                    var confirm_path = '.action_new_parent_post_confirm_children';
                } else {
                    var confirm_path = '.action_new_parent_post_confirm';
                }
                $(".action-wine-name").html(data.wine_name);
                $(".action-wine-author-avatar-url").attr('alt', data.wine_author);
                $(".action-wine-author-url").attr('href', data.wine_author_url);
                $(".action-wine-author-avatar-url").attr('src', data.wine_author_avatar_url)
                $(".find-pprf").html(thys.postStatus)
                thys.massOperationConfirm(
                    url_mop_change_parent_post,
                    mop_ser_array,
                    confirm_path,
                    '.ui-bootbox-new-parent-post-confirm',
                    '.ui-bootbox-new-parent-post-cancel'
                );

            },
            error: function(data){
                console.warn(data);
            }
        });
    } else {
        this.massOperation(
            url_mop_change_parent_post,
            mop_ser_array
        );
    }

    this.uncheck_define_as_child();
    this.uncheck_mop_parent_post();
    this.uncheck_mop_star_review();

    this.show_pro_selector_wm();
    this.show_pro_selector_wine();

    return false;
}



// TODO: in the later version I want to make this DataTableFactory independent from wineposts, but for now,
// TODO: mop_init which initializes parent-selector etc will be just setup here directly
DataTableFactory.prototype.mop_init = function() {
    var thys = this;
    this.nat_oth_path = this.action_panel_path + " [name='nat_oth']";
    this.nat_oth_checked_path = this.action_panel_path + " [name='nat_oth']:checked";
    this.mop_define_as_child_path = this.action_panel_path + " .mop_define_as_child";
    this.mop_change_parent_cancel_path = this.action_panel_path + " .mop_ui-bootbox-change-parent-cancel";
    this.mop_change_parent_confirm_path = this.action_panel_path + " .mop_ui-bootbox-change-parent-confirm";
    this.mop_not_wine_path = this.action_panel_path + " .ui-bootbox-mop-not-wine";
    this.display_natural_path = this.action_panel_path + " .display-natural";
    this.display_other_path = this.action_panel_path + " .display-other";
    this.wine_selector_path = this.action_panel_path + ' .mop_jq-validation-select2-multi';
    this.wine_selector_container_path = this.action_panel_path + " .mop_select2-jq-validation-select2-multi-container";
    this.wm_selector_path = this.action_panel_path + ' .mop_jq-validation-select2';
    this.wm_selector_container_path = this.action_panel_path + " .mop_select2-jq-validation-select2-container";
    this.mop_parent_post_path = this.action_panel_path + " .mop_parent_post";
    this.mop_star_review_path = this.action_panel_path + " .mop_star_review";
    this.pro_selector_wm_path = this.action_panel_path + " .pro_selector_wm";
    this.pro_selector_wine_path = this.action_panel_path + " .pro_selector_wine";
    this.pro_selector_wine_status_path = this.action_panel_path + " .wine_status";



    $(this.nat_oth_path).unbind('click');
    $(this.mop_define_as_child_path).unbind('click');
    $(this.mop_change_parent_cancel_path).unbind('click');
    $(this.mop_change_parent_confirm_path).unbind('click');
    //    $("#ui-bootbox-mop-update").unbind('click');

    this.uncheck_define_as_child();
    this.uncheck_mop_parent_post();
    this.uncheck_mop_star_review();

    this.show_pro_selector_wm();
    this.show_pro_selector_wine();

    $(this.nat_oth_path).click(function(){
        
            var which = $(thys.nat_oth_checked_path).val();
            if(which == 'other') {
                thys.postStatus = "Referrer";
                sel_display_natural = false;
                $(thys.display_natural_path).hide();
                $(thys.display_other_path).show();
                $('.mop_parent_post').addClass('other')
                $('.mop_parent_post').removeClass('natural')
                if($(this.mop_parent_post_path).is(":checked") || thys.is_mop_parent_post_checked()){
                    $(thys.pro_selector_wine_status_path).show();
                }else{
                    $(thys.pro_selector_wine_status_path).hide();
                }
                
            } else {
                thys.postStatus = "Parent Post";
                sel_display_natural = true;
                $('.mop_parent_post').removeClass('other')
                $('.mop_parent_post').addClass('natural')
                $(thys.display_natural_path).show();
                $(thys.display_other_path).hide();
                $(thys.pro_selector_wine_status_path).hide();
            }
    });

    
    // if($(this.nat_oth_path).is(":checked")) {
    //     console.log('checked')
    // }else{
    //     console.log('not checked');
    //     $('.mop_define_as_child').click(function(){
    //         if($(this).is(':checked')){
    //             $('.nat_oth_n').prop('checked')
    //         }
    //     })
    // }

    $(this.mop_change_parent_cancel_path).click(function(){
        thys.uncheck_define_as_child();
        thys.uncheck_mop_parent_post();
        thys.show_pro_selector_wm();
        thys.show_pro_selector_wine();
        $(thys.action_panel_path).hide();
        return false;
    });

    // click on "define as child" checkbox
    $(this.mop_define_as_child_path).click(function() {
        var define_as_child_check = thys.is_define_as_child_checked();
        var is_parent_post_check = thys.is_mop_parent_post_checked();
        if(define_as_child_check) {
            thys.show_pro_selector_wine();
        }
        if(define_as_child_check && is_parent_post_check) {
            thys.uncheck_mop_parent_post();
        }

       
    });

    $(".mop_define_as_child").click(function(){
        if($(this).is(":checked")){
            $(this).parents('.action-top-container').find(".nat_oth_n").siblings("label").trigger('click');
            $('.mop_parent_post').removeClass('other')
        }
        else{
            $(".nat_oth_n").prop("checked",false);
        }
    })

    // if($(this.mop_parent_post_path).hasClass("other")){
    //     $(this.mop_parent_post_path).click(function() {
    //         if($(this).is(":checked")) {
    //             $(".nat_oth_o").siblings("label").trigger('click');
    //         }else{
    //             $(".nat_oth_o").prop("checked",false)
    //         }
    //     });
    // }else{
    //     $(this.mop_parent_post_path).click(function() {
    //         if($(this).is(":checked")) {
    //             $(".nat_oth_n").siblings("label").trigger('click');
    //         }else{
    //             $(".nat_oth_n").prop("checked",false)
    //         }
    //     });
    // }

  

    // click on "parent post" checkbox
    $(this.mop_parent_post_path).change(function() {

        var which = $(this.mop_parent_post_path).val();
        var parent_post_check = thys.is_mop_parent_post_checked();
        var define_as_child_check = thys.is_define_as_child_checked();


        if(!$(this).hasClass("other")){
            if($(this).is(":checked")){
                $(this).parents('.action-top-container').find(".nat_oth_n").siblings("label").trigger('click');
            }else{
                $(this).parents('.action-top-container').find(".nat_oth_n").prop("checked",false)
            }
        }

        if($(this).is(":checked")) {
            $('.pro_selector_wine').hide();
            if($(thys.nat_oth_checked_path).val()  == 'other'){
                $(thys.pro_selector_wine_status_path).show();
            }else{
                $(thys.pro_selector_wine_status_path).hide();
            }
           
        } else {
            $('.pro_selector_wine').show();
            $(thys.pro_selector_wine_status_path).hide();
        }
        if(parent_post_check && define_as_child_check) {
            thys.uncheck_define_as_child();
        }
    });

    $('.other').click(function(){
        if($(this).is(":checked")){
            $(".nat_oth_o").siblings("label").trigger('click');
        }else{
            $(".nat_oth_o").prop("checked",false)
        }
    })
    // $('input[name="mop_parent_post"]').click(function() {
    //     var parent_post_check = thys.is_mop_parent_post_checked();
    //     var define_as_child_check = thys.is_define_as_child_checked();
    //     var which = $(this).val();
    //     console.log(which)
    //     if($(this).is(':checked') && which == "Referrer") {
    //         $('.pro_selector_wine').hide();
    //         $(thys.pro_selector_wine_status_path).show();
    //     } else{
    //         $(thys.pro_selector_wine_status_path).hide();
    //     }
    //     if($(this).is(':checked') && which == "parentPost") {
    //         thys.hide_pro_selector_wine();
    //     }else{
    //         thys.show_pro_selector_wine();
    //     }
    //     if(parent_post_check && define_as_child_check) {
    //         thys.uncheck_define_as_child();
    //     }
    // });

    // click on the green "CONFIRM" button
    $(this.mop_change_parent_confirm_path).click(function(){
            thys.do_mop_wineposts();
            return false;
    });


    var select_wine = $(this.wine_selector_path).select2({
        allowClear: true,
        width: '100%',
        placeholder: 'Select Wine...'
    }).change(function(){
        $(this.wine_selector_container_path).css('border', 'none');
    });

    var select_wm = $(this.wm_selector_path).select2({
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
        var is_parent_post = $(thys.mop_parent_post_path).prop('checked')? true: false;
        if(val && !is_parent_post){
            $.ajax({
                type: "POST",
                dataType: "json",
                url: url_mop_change_parent_post_wine_list,
                data: {
                    "winemaker_id": val
                },
                success: function(data) {
                    $(thys.wine_selector_path).empty();
                    if (data.items) {
                        select_wine = $(thys.wine_selector_path).select2({
                            "data": data.items,
                            allowClear: true,
                            width: '100%',
                            placeholder: 'Select Wine...'
                        }).change(function(){
                            $(thys.wine_selector_container_path).css('border', 'none');
                        });
                    }
                },
                error: function(data){
                    console.warn(data);
                }
            });
        }else{
            $(thys.wine_selector_path).empty();
        }
    });
}


DataTableFactory.prototype.setupCallbacks = function() {
    // TODO: in the later version I want to make this DataTableFactory independent from wineposts, but for now,
    // TODO: mop_init which initializes parent-selector etc will be just called here directly
    this.mop_init();
}


DataTableFactory.prototype.bindMassOperationConfirm = function(button_path, url, extra_ser_array,
        confirm_panel_path, confirm_button_path, cancel_button_path) {
    var thys = this;
    $(document).on('click', button_path, function() {
        const rawText = (button_path.split("-")[button_path.split("-").length - 1]);
        let txt = '';
        switch(rawText) {
            case 'publish': 
                txt = "Natural";
                break;
            case 'bioorg':
                txt = 'Bio-Organic';
                break;
            case 'unpublish':
                txt = 'Draft';
                break;
            case 'indoubt':
                txt = 'In Doubt';
                break;
            case 'investigate':
                txt = 'To Investigate';
                break;
            case 'undelete' :
                txt = 'Undelete';
                break;
            case 'wine' :
                txt = 'Not Wine';
                break;
        }
        $(thys.statusText).html(txt)
        thys.massOperationConfirm(url, extra_ser_array, confirm_panel_path, confirm_button_path, cancel_button_path);
        return false;
    });
}


DataTableFactory.prototype.bindMassOperationNonConfirm = function(button_path, url, extra_ser_array) {
    var thys = this;
    $(document).on('click', button_path, function() {
        thys.massOperation(url, extra_ser_array);
        return false;
    });
}


DataTableFactory.prototype.setupMassOperations = function() {
    var thys = this;
    if(this.mass_operations != undefined && this.mass_operations != null && this.mass_operations.length > 0) {
        for(var i in this.mass_operations) {
            var op = this.mass_operations[i];
            if (op['button_path'] == undefined ||
                    op['button_path'] == null ||
                    op['button_path'] == '' ||
                    op['url'] == undefined ||
                    op['url'] == null ||
                    op['url'] == '') {
                continue;
            }
            var button_path_full = this.action_panel_path + " " + op['button_path'];
            $(button_path_full).unbind('click');
            if (op['is_confirm'] != undefined && op['is_confirm'] != null && op['is_confirm'] == true ) {
                if(op['confirm_panel_path'] == undefined ||
                        op['confirm_panel_path'] == null ||
                        op['confirm_panel_path'] == '' ||
                        op['confirm_button_path'] == undefined ||
                        op['confirm_button_path'] == null ||
                        op['confirm_button_path'] == '' ||
                        op['cancel_button_path'] == undefined ||
                        op['cancel_button_path'] == null ||
                        op['cancel_button_path'] == '') {
                    continue;
                }
                var confirm_panel_path_full = this.action_panel_path + " " + op['confirm_panel_path'];
                var confirm_button_path_full = this.action_panel_path + " " + op['confirm_button_path'];
                var cancel_button_path_full = this.action_panel_path + " " + op['cancel_button_path'];
                
                this.bindMassOperationConfirm(button_path_full, op['url'], op['extra_ser_array'],
                    confirm_panel_path_full, confirm_button_path_full, cancel_button_path_full);
            } else {
                this.bindMassOperationNonConfirm(button_path_full, op['url'], op['extra_ser_array']);
            }
        }
        if(this.mop_init != undefined && this.mop_init != null) {
            this.mop_init();
        }
        $(this.action_cancel_selection_path).click(function(){
            thys.cancelSelection();
            return false;
        });
    }
}


DataTableFactory.prototype.massOperationConfirm = function(url, extraSerArray, confirm_panel_path,
        confirm_button_path, cancel_button_path) {
    var thys = this;

    $(this.action_main_path).hide();
    $(confirm_panel_path).show();
    $(confirm_button_path).unbind("click");
    $(cancel_button_path).unbind("click");

    $(confirm_button_path).click(function(){
        thys.massOperation(url, extraSerArray);
       
        return false;
    });
    $(cancel_button_path).click(function(){
        if(cancel_button_path === ".ui-bootbox-new-parent-post-cancel"){
            $(thys.display_natural_path).show();
            $(thys.display_other_path).hide();
            $(thys.nat_oth_path).prop('checked', false);
        }
        $(confirm_panel_path).hide();
        $(thys.action_main_path).show();
        return false;
    });

    return false;
}


DataTableFactory.prototype.massOperation = function(url, extraSerArray) {
    var thys = this;
    var serArray = $(this.all_checked_row_ids_path).serializeArray();
    if (extraSerArray != undefined && Array.isArray(extraSerArray) && extraSerArray.length > 0) {
        serArray = serArray.concat(extraSerArray);
    }
    $.ajax({
        type: "POST",
        url: url,
        data: serArray,
        success: function(data) {
            thys.refreshList();

            $(thys.toggle_all_element_path).prop('checked', false);
            $(thys.action_confirm_path).hide();
            $(thys.action_panel_path).hide();
            if (thys.entities != undefined && thys.entities != null &&
                    $(thys.getMenuNumPath(thys.entities)).length > 0 && data['count']!=undefined &&
                    data['count']!=null && data['count']!='') {
                $(thys.getMenuNumPath(thys.entities)).html(data['count']);
            }
        },
        error: function(data){
            console.warn(data);
        }
    });
    return false;
}


DataTableFactory.prototype.draw = function() {
    var thys = this;
    thys.datatable_element = $(this.table_path).DataTable({
        "processing": true,
        "serverSide": true,
        "searchDelay": 1000,
        "paging": true,
        oLanguage: {sProcessing: '<div class="spinner-dots-list"><img src="/static/pro_assets/img/preloading.gif" alt="Processing Data" width="60" height="100"></div>'},
        //   "bFilter": false,

        dom: "<'table-header'<'row d-flex items-center m-0'<'col-sm-6 p-0'<'table-caption text-left'>><'col-sm-6 p-0 d-flex justify-end'l<'positionFilter'>>>>" +
        "<'row m-0'<'col-sm-12 pr-1'tr>>" +
        "<'table-footer'<'row d-flex items-center m-0 '<'col-sm-6 text-left'i><'col-sm-6 text-right'p>>>",
        ajax: $.fn.dataTable.pipeline({
            "url": thys.url,
            "type" : "POST",
            // "data": function (d) {
            //    d.extra_search = $('#search_all').val();
            // }
        }),
        'bAutoWidth' : false,
        "aLengthMenu": [10, 25, 50, 100, 500, 1000 ],
        //"iDisplayLength": 50,
        "order": this.default_order,
        columns: this.columns,

        drawCallback: function(settings) {
            $(thys.tooltip_path).tooltip();
            $(thys.all_row_ids_path).click(function() {
                $(thys.display_natural_path).show();
                $(thys.display_other_path).hide();
                $(thys.nat_oth_path).prop('checked', false);
                thys.handleActionFooter();
            });

            $(thys.visible_images_path).unveil();
            // var total_records = thys.datatable_element.fnSettings().fnRecordsTotal(); // version for no-pipeline
            var total_records = settings._iRecordsTotal;
            var search_value = thys.datatable_element.data().search();
            if (search_value != undefined && search_value != null && search_value != ""){
                thys.title_format_params['search'] = search_value;
            }else{
                thys.title_format_params['search'] = "";
            }
            thys.title_format_params['count'] = total_records;

            // if (search_value != undefined && search_value != null && search_value != "") {
            //     $('.positionFilter').append('<i class="clear-search">x</i>');
            // } else {
            //     $('.positionFilter').find('.clear-search').remove();
            // }

            thys.setTitle();

            var paginate_button_count = $(thys.paginate_button_path).not(thys.paginate_button_previous_path)
                .not(thys.paginate_button_next_path).length;
            if (paginate_button_count < 2){
                $(thys.paginate_button_path).hide();
            }else{
                $(thys.paginate_button_path).show();
            }
        }
    });

    this.setTitle();
    $(this.filter_input_path).attr('placeholder', 'Search...');

    $(this.toggle_all_element_path).click(function() {
        var is_checked = $(this).prop('checked');
        $(thys.all_checkboxes_path).prop('checked', is_checked);
        thys.handleActionFooter();
    });

    this.setupMassOperations();
    this.setupCallbacks();


    //   $(this.filter_input_path).unbind();
    //   $(this.filter_input_path).bind('keyup', function(e) {
    //       if (this.value.length > 2 || this.value.length === 0) {
    //           thys.datatable_element.search(this.value).draw(true);
    //       }
    //   });
  
  
    function debounce(func, timeout = 1000){
        let timer;
        return (...args) => {
          clearTimeout(timer);
          timer = setTimeout(() => { func.apply(this, args); }, timeout);
        };
    }
      
    function saveInput(search){
        console.log(search);
        thys.datatable_element.search(search).draw(true);
        
    }
    const processChange = debounce((search) => saveInput(search));


    $('#' + this.table_id + '_wrapper').find('.positionFilter').html('<input type="text" class="form-control" placeholder="Search" id="' + this.searchId +  '"><i class="clear-search">x</i>')


    $(document).on('keyup', '#' + this.searchId, function() {
        var $this = $(this);
        var value = $this.val();
        if(value.length > 0){
            $this.parents(".positionFilter").addClass("searched")
        }else{
            $this.parents(".positionFilter").removeClass("searched")
        }
        processChange(value);
    });


    
    init.push(function () {
        $(thys.tooltip_path).tooltip();
    });

    if (thys.action_panel_id == 'action-owners') {
        window.ownersDataTableDrawElement = thys.datatable_element;
    }

    if (thys.action_panel_id == 'action-users') {
        window.usersDataTableDrawElement = thys.datatable_element;
    }
    if (thys.action_panel_id == 'action-geolocated') {
        window.geolocatedDataTableDrawElement = thys.datatable_element;
    }

    if (thys.action_panel_id == 'action-all') {
        window.allDataTableDrawElement = thys.datatable_element;
    }
}
