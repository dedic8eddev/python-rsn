var ImageManager = function(element, options){
    options = options || {};

    if(!options.url_current_images){
        $.error("url_current_images is missing");
    }
    if(!options.url_delete_image){
        $.error("url_delete_image is missing");
    }

    this.options = $.extend({}, this.defaults, options);
    this.element = $(element);

//    this.options.current_images_request_data = options.current_images_request_data || {};
    this.options.delete_image_request_data = options.delete_image_request_data || {};

    if (this.options.refresh_on_init) {
        this.refreshImages();
    }

}

ImageManager.prototype = {
    constructor: ImageManager,

    options: {},

    callback: null,

    defaults: {
        request_method: "POST",
        request_data_type: "html",

        image_identifier_xhr_field: "filename",

        image_identifier_tag: "data-image-file",
        image_list_item_selector: ".image-list-item",
        delete_confirmation_message: "Do you really want to delete this image? ",
        refresh_on_init: true,

        b_sortable: null,
        remove_btn_selector: 'p'
    },

    updateOptions: function(options){
        for (option_id in options){
            option_data = options[option_id];
            this.options[option_id] = option_data;
        }
        this.refreshImages();
    },

    handleImages: function() {
        var this_image_manager = this;
        var image_selector = $(this.element).find(this.options.image_list_item_selector);
        var remove_btn_selector = this.options.remove_btn_selector;

        $(image_selector).each(function(index){
            $(this).find(remove_btn_selector).unbind('click');

            var img_element = this;

            $(this).find(remove_btn_selector).click(function(){
                this_image_manager.deleteImageByElement(img_element);
                return false;
            });
        });

        if(this_image_manager.options.callback){
            this_image_manager.options.callback();
        }

    },

    deleteImageByElement: function(img_element){
        var file_element_selector = "img["+this.options.image_identifier_tag+"]";
        var file_element = $(img_element).find(file_element_selector);
        var image_identifier = $(file_element).attr(this.options.image_identifier_tag);

        x = confirm(this.options.delete_confirmation_message + "(" +image_identifier+")");

        if(!x){
            return false;
        }

        var add_req_data = {};
        add_req_data[this.options.image_identifier_xhr_field] = image_identifier;

        if (this.options.b_sortable) {
            if (this.options.temp_image_ordering_field) {
                add_req_data["temp_image_ordering"] = this.options.b_sortable.get_items_string_old();
            }
        }

        var req_data = $.extend(this.options.delete_image_request_data, add_req_data);

        $.ajax({
            context     : this,
            type        : this.options.request_method,
            url         : this.options.url_delete_image,
            data        : req_data,
            dataType    : this.options.request_data_type,

            success: function(data) {
                $(this.element).html(data);
                this.handleImages();
            },
            error: function(data){
                console.warn(data);
            }
        });

        return false;
    },

    refreshImagesWithHtml: function(html_data){
        $(this.element).html(html_data);
        this.handleImages();

    },

    refreshImages: function() {
        var add_req_data = {};
        if (this.options.b_sortable && this.options.temp_image_ordering_field) {
            add_req_data["temp_image_ordering"] = this.options.b_sortable.get_items_string_old();
        }


        var req_data = $.extend(this.options.delete_image_request_data, add_req_data);
        this.handleImages();

        $.ajax({
            context     : this,
            type        : this.options.request_method,
            url         : this.options.url_current_images,
            data        : req_data,
            dataType    : this.options.request_data_type,

            success: function(data) {
                $(this.element).html(data);
                this.handleImages();
            },
            error: function(data){
                console.warn(data);
            }
        });
    }

};
