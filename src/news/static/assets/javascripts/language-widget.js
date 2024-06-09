
var PDG_Widget1 = function (options){
    options = options || {};
    this.options = $.extend({}, this.defaults, options);
}
PDG_Widget1.prototype = {
    constructor: PDG_Widget1,

    options: {},

    defaults: {
        pdg_top_element: '.pdg-language-group',
        pdg_display_selected_element: ".pdg-language-group .pdg-language-selected",
        pdg_dropdown_menu_element: ".pdg-language-group .dropdown-menu",
        pdg_option_element: ".pdg-language-group .dropdown-menu .pdg-language-option",
        pdg_open_element: ".pdg-language-group .pdg-arrow",
        pdg_value_field_id: "id_language",
    },


    set_current_value: function (value){
        $("#" + this.options.pdg_value_field_id).val(value);
    },

    get_current_value: function (){
        return $("#" + this.options.pdg_value_field_id).val();
    },
    refresh: function() {
        var $pdg_selected = $(this.options.pdg_display_selected_element);

        var current_value = this.get_current_value();
        $(this.options.pdg_option_element).each(function(){
            var pdg_option_val = $(this).attr('data-val');
            var pdg_option_text = $(this).text();
            if (pdg_option_val == current_value){
                $pdg_selected.attr('data-val', pdg_option_val);
                $pdg_selected.attr('class', "btn btn-rounded pdg-language-selected ");
                $pdg_selected.text(pdg_option_text);
                $(".label-language-description").text(pdg_option_val.toUpperCase())
                $(".label-language-title").text(pdg_option_val.toUpperCase())
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
            thys.set_current_value(pdg_option_val);
            $(thys.options.pdg_open_element).trigger('click');

            thys.refresh();

            return false;
        });
        this.refresh();
    }
};
