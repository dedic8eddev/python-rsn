var SortableManager = function(element_id, options){
    options = options || {};

    this.already_created = false;
    this.options = $.extend({}, this.defaults, options);

//    element_id = "#current-images-inside";
    this.element_id = element_id;

    this.init();
}

SortableManager.prototype = {
    constructor: SortableManager,
    options: {},
    callback: null,


    defaults: {
        url_update_ordering_ajax: null,
        ordering_field_id: 'id_image_ordering',
        parent_item_id: null,
//        request_method: "POST",
//        request_data_type: "html",
    },

    updateOptions: function(options){
        for (option_id in options){
            option_data = options[option_id];
            this.options[option_id] = option_data;
        }
    },

    init: function (){
        var thys = this;

        this.sortable = $(this.element_id).sortable({

            create: function( event, ui ) {
                if(thys.already_created){
                    var old_val = thys.get_items_string_old();
                    var items = thys.get_items();

                    $("#" + thys.options.ordering_field_id).val(thys.get_items_string());
                }else{
                    thys.already_created = true;
                }
            },

            update: function ( event, ui) {
                var items = thys.get_items();

                // parent item id - permanent images
                if(thys.options.parent_item_id && thys.options.url_update_ordering_ajax){
                    var data_out = []
                    data_out.push({
                        'name': 'parent_item_id',
                        'value': thys.options.parent_item_id
                    });
                    data_out.push({
                        'name': 'ids',
                        'value': items.join(',')
                    });

                    $.ajax({
                        type        : "POST",
                        url         : thys.options.url_update_ordering_ajax,
                        data        : data_out,
                        success: function(data) {

                        },
                        error: function(data){
                            console.warn(data);
                        }
                    });

                // NO parent item id - temp images
                } else {
                    $("#" + thys.options.ordering_field_id).val(items.join(','));
                }

            }


        });
    },

    get_items: function (){
        var items = $(this.element_id).sortable("toArray", {attribute: 'cnt-data-image-file'});
        return items;
    },

    get_items_string: function (){
        var items = $(this.element_id).sortable("toArray", {attribute: 'cnt-data-image-file'});

        if (items) {
            return items.join(',');
        }else{
            return '';
        }
    },

    get_items_string_old: function(){
        return $("#" + this.options.ordering_field_id).val();
    }

}
