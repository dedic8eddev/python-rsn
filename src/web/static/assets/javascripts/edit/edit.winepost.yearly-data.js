init.push(function(){
    $("#id_year").change(function() {
        var year = $(this).val();
        YearlyDataManager.switch_year($(this).val());
    });

    $("#id_grape_variety").blur(function() {
        YearlyDataManager.update_grape_variety($(this).val());
    });

    $("#id_free_so2").blur(function() {
        YearlyDataManager.update_free_so2($(this).val());
    });

    $("#id_total_so2").blur(function() {
        YearlyDataManager.update_total_so2($(this).val());
    });

    YearlyDataManager.fetch_from_db();
});
