
var PDG_Widget = function (options){
    options = options || {};
    this.options = $.extend({}, this.defaults, options);
}


PDG_Widget.prototype = {
    constructor: PDG_Widget,

    options: {},

    defaults: {
        pdg_top_element: '.pdg-group',
        pdg_display_selected_element: ".pdg-group .pdg-selected",
        pdg_dropdown_menu_element: ".pdg-group .dropdown-menu",
        pdg_option_element: ".pdg-group .dropdown-menu .pdg-option",
        pdg_open_element: ".pdg-group .pdg-arrow",
        pdg_value_field_id: "id_status",
    },


    set_current_value: function (value){
        $("#" + this.options.pdg_value_field_id).val(value);
    },

    get_current_value: function (){
        return $("#" + this.options.pdg_value_field_id).val();
    },

    refresh: function() {
        var $pdg_selected = $(this.options.pdg_display_selected_element);
        var $pdg_dropdown = $(this.options.pdg_dropdown_menu_element);

        var current_value = this.get_current_value();

        $(this.options.pdg_option_element).each(function(){
            var pdg_option_val = parseInt($(this).attr('data-val'));
            var pdg_option_text = $(this).text();
            var pdg_option_class = $(this).attr('data-class');

            if (pdg_option_val == parseInt(current_value)){
                $pdg_selected.attr('data-val', pdg_option_val);
                $pdg_selected.attr('class', "btn pdg-selected "+pdg_option_class);
                $pdg_selected.text(pdg_option_text);
                $(this).hide();
            }else{
                $(this).show();
            }
        });
    },

    init: function() {
        var thys = this;

        $(this.options.pdg_option_element).click(function(){
            var pdg_option_val = $(this).attr('data-val');
            var pdg_option_text = $(this).text();

            thys.set_current_value(pdg_option_val);
            $(thys.options.pdg_open_element).trigger('click');

            thys.refresh();

            return false;
        });

        this.refresh();
    }
};
