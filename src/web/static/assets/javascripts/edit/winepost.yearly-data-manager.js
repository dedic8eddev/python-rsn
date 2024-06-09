var YearlyDataManager = {
    data: {
    },

    get_year: function() {
        return $("#id_year").val();
    },

    // get_empty_yearly_data: function(){
    //     return {
    //         "free_so2": "",
    //         "total_so2": "",
    //         "grape_variety": ""
    //     };
    // },

    delete_year: function(year) {
//        if(year == undefined || year == null) {
//            return;
//        }
        if (YearlyDataManager.data[year] == undefined || YearlyDataManager.data[year] == null) {
            return;
        }

        if (!confirm("Are you sure you want to erase [" + year + "]")) {
            return;
        }

        $.ajax({
            type        : "POST",
            url         : url_delete_yearly_data_ajax,
            data        : {
                "winepost_id": winepost_id,
                "year": year
            },
            dataType    : 'json',
            success: function(data) {
                if(data.action == 'RELOAD_DRAFT') {
                    alert("You have changed the grape variety of this child post,\nso its status was"
                          + "changed to DRAFT. The page will be reloaded.")
                    location.href = url_this_winepost_edit;
                }
                else if(data.action != 'ERROR') {
                    YearlyDataManager.data = data.yearly_data;
                    YearlyDataManager.display_all_years();
                }
            },
            error: function(data){
                console.warn(data);
            }
        });
    },

    get_yearly_data: function(year) {
//        if(year == undefined || year == null) {
//            return;
//        }
        if (YearlyDataManager.data[year] != undefined && YearlyDataManager.data[year] != null) {
            return YearlyDataManager.data[year];
        }else {
            return YearlyDataManager.get_empty_yearly_data();
        }
    },

    set_yearly_data: function(year, yearly_data) {
        YearlyDataManager.data[year] = yearly_data;
        YearlyDataManager.store_in_db();
        YearlyDataManager.display_all_years();
    },

    switch_year: function(year) {
//        if(year == undefined || year == null || year == '' || isNaN(year) || parseInt(year) < 1) {
//            return;
//        }
        yd = YearlyDataManager.get_yearly_data(year);
        $("#id_grape_variety").val(yd['grape_variety']);
        $("#id_free_so2").val(yd['free_so2']);
        $("#id_total_so2").val(yd['total_so2']);
        $("#id_year").val(year);
        YearlyDataManager.display_all_years();
    },

    update_feature: function(feature, val) {
        var year = YearlyDataManager.get_year();
        if(year == undefined || year == null || year == '' || isNaN(year) || parseInt(year) < 1) {
            return;
        }
        var yd = YearlyDataManager.get_yearly_data(year);
        yd[feature] = val;
        YearlyDataManager.set_yearly_data(year, yd);
    },

    update_free_so2: function(val) {
        YearlyDataManager.update_feature('free_so2', val);
    },

    update_total_so2: function(val) {
        YearlyDataManager.update_feature('total_so2', val);
    },

    update_grape_variety: function(val) {
        YearlyDataManager.update_feature('grape_variety', val);
    },


    display_all_years: function() {
        if(!is_parent_post) {
            return;
        }

        var years = [];
        for(i in YearlyDataManager.data) {
            years.push(i);
        }
        years.sort();
        years.reverse();
        var urls = '<ul>';
        var val_this_year = YearlyDataManager.get_year();
        var urls_array = [];
        for(i in years) {
            if (val_this_year == years[i]) {
                var class_year = 'wp-sel-year';
            } else {
                var class_year = '';
            }
            if (is_parent_post) {
                var url = '<li><a href="#" class="' + class_year +
                            ' year-item" onclick="YearlyDataManager.switch_year(' +
                                years[i] + '); return false;">' + years[i] + '</a>' +
                            '<a href="#" title="Delete vintage" class="year-delete-btn" onclick="YearlyDataManager.delete_year(' +
                                years[i] + '); return false;">' +
                            '<i class=" fa fa-times-circle"></i></a>' +
                            '</li>';
            } else {
                var url = '<li><a href="#" class="' + class_year +
                            '" onclick="YearlyDataManager.switch_year(' +
                                years[i] + '); return false;">' + years[i] + '</a>' +
                            '</li>';
            }
            urls_array.push(url);
        }
        urls += urls_array.join('<li class="year-item-sep">-</li>');
        urls += '</ul>';
        $("#all_years").html(urls);
    },

    fetch_from_db: function () {
        $.ajax({
            type        : "POST",
            url         : url_fetch_yearly_data_ajax,
            data        : {
                "winepost_id": winepost_id
            },
            dataType    : 'json',
            success: function(data) {
                YearlyDataManager.data = data;
                YearlyDataManager.display_all_years();
            },
            error: function(data){
                console.warn(data);
            }
        });
    },

    store_in_db: function() {
        $.ajax({
            type        : "POST",
            url         : url_update_yearly_data_ajax,
            data        : {
                "winepost_id": winepost_id,
                "cur_year": $("#id_year").val(),
                "cur_grape_variety": $("#id_grape_variety").val(),
                "cur_free_so2": $("#id_free_so2").val(),
                "cur_total_so2": $("#id_total_so2").val()
            },
            dataType    : 'json',
            success: function(data) {
                if(data.action == 'RELOAD_DRAFT') {
                    alert("You have changed the grape variety of this child post,\nso its status was"
                          + "changed to DRAFT. The page will be reloaded.")
                    location.href = url_this_winepost_edit;
                }
                else if(data.action != 'ERROR') {
                    YearlyDataManager.data = data.yearly_data;
                    YearlyDataManager.display_all_years();
                }
            },
            error: function(data){
                console.warn(data);
            }
        });
    }
};
