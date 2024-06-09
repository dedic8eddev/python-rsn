//var b_datatable_referees = null;
//
//init.push(function () {
//    vuforia_scans_total = 0;
//
//    var table_id = 'jq-datatables-referee';
//    var action_panel_id = 'action-owners';
//    var table_label = 'Latest published referees:';
//    var table_columns = [
//                { "data" : "checkbox_id", orderable: false },
//                { "data" : "author_img_html", orderable: true },
//                { "data" : "img_html" },
//                { "data" : "title" },
//
//                { "data" : "description" },
//                { "data" : "status_html" },
//                { "data" : "winemaker_name" },
//                { "data" : "domain" },
//
//                { "data" : "designation" },
//                { "data" : "grape_variety" },
//                { "data" : "region" },
//                { "data" : "year" },
//
//                { "data" : "color_text" },
//                { "data" : "sparkling_html" },
//                { "data" : "place_html"},
//
//                { "data" : "comment_number" },
//                { "data" : "likevote_number" },
//                { "data" : "drank_it_too_number" }
//            ];
//    var table_default_order = [[ 4, "asc" ]];
//    var table_mass_operations = [
//        {
//            "button_path": ".ui-bootbox-publish",
//            "url": url_wineposts_publish_ajax,
//            "extra_ser_array": null
//        },
//        {
//            "button_path": ".ui-bootbox-unpublish",
//            "url": url_wineposts_unpublish_ajax,
//            "extra_ser_array": null
//        },
//        {
//            "button_path": ".ui-bootbox-indoubt",
//            "url": url_wineposts_set_in_doubt_ajax,
//            "extra_ser_array": null
//        },
//        {
//            "button_path": ".ui-bootbox-bioorg",
//            "url": url_wineposts_set_bio_organic_ajax,
//            "extra_ser_array": null
//        },
//        {
//            "button_path": ".ui-bootbox-undelete",
//            "url": url_wineposts_undelete_ajax,
//            "extra_ser_array": null
//        },
//        {
//            "button_path": ".ui-bootbox-delete",
//            "url": url_wineposts_delete_ajax,
//            "extra_ser_array": null,
//            "is_confirm": true,
//            "confirm_panel_path": ".action_delete_confirm",
//            "confirm_button_path": ".ui-bootbox-delete-confirm",
//            "cancel_button_path": ".ui-bootbox-delete-cancel"
//        },
//        {
//            "button_path": ".ui-bootbox-refuse",
//            "url": url_wineposts_refuse_ajax,
//            "extra_ser_array": null,
//            "is_confirm": true,
//            "confirm_panel_path": ".action_refuse_confirm",
//            "confirm_button_path": ".ui-bootbox-refuse-confirm",
//            "cancel_button_path": ".ui-bootbox-refuse-cancel"
//        }
//    ];
//
//    b_datatable_referees = new DataTableFactory(
//        table_id,
//        url_get_winepost_referee_items,
//        table_label,
//        table_columns,
//        table_default_order,
//        table_mass_operations,
//        action_panel_id,
//        'wineposts'
//    );
//
//    b_datatable_referees.draw();
//});
//
//init.push(function () {
//    $("#id_is_parent_post").unbind('click');
//    $("#define_as_child").unbind('click');
//
//    $("#id_is_parent_post").click(function(){
//        var is_checked = $(this).prop('checked');
//        console.log('checked: ' + is_checked);
//
//        if(is_checked){
////            if(wm_natural) {
//            if(sel_display_natural) {
//                pdg_widget.set_current_value(20);
//                pdg_widget.refresh();
//            }
//
//            $('#jq-datatables-referee').DataTable().ajax.reload(function (json) {
//                console.log("JSON");
//                console.log(json);
//                if((json.data != undefined) && (json.data.length > 0)){
//                    $("#actionpost").show();
//                }
//            });
//        }else{
//            $("#actionpost").hide();
//        }
//    });
//
//    $("#define_as_child").click(function(){
//        var is_checked = $(this).prop('checked');
//        console.log('checked: ' + is_checked);
//
//        if(is_checked){
//            $("#actionpostparent").show();
//        }else{
//            $("#actionpostparent").hide();
//        }
//    });
//
//
//});