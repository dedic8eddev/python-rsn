var all_stats = {};
var chart_venue = null;
var chart_from = null;
var donut_venue = null;
var donut_from = null;


function get_ym_label(year, month) {
    var ym_label = "" + year + "-" + ("0" + month).slice(-2);
    return ym_label;
}


function get_x_label_format(x) {
    var month = x.getMonth() + 1;
    var year = x.getFullYear();
    var ym_label = get_ym_label(year, month);
    return all_stats['yms_labels_all_years'][ym_label];
}


function get_date_format(x) {
    var month = new Date(x).getMonth() + 1;
    var year = new Date(x).getFullYear();
    var ym_label = get_ym_label(year, month);
    return all_stats['yms_labels_all_years'][ym_label];
}


function update_morris_chart_venue(stats_for_year) {
    chart_venue.setData(stats_for_year['tap_venue_list']);
}


function update_morris_chart_from(stats_for_year) {
    chart_from.setData(stats_for_year['tap_from_list']);
}


function update_morris_donut_venue(tap_data_for_period) {
    donut_venue.setData([
        {label: 'Website', value: tap_data_for_period['tap_venue_website'], color: '#55aff9', fillOpacity: '0.8'},
        {
            label: 'Get Direction',
            value: tap_data_for_period['tap_venue_direction'],
            color: '#df91f1',
            fillOpacity: '0.8'
        },
        {label: 'Phone Calls', value: tap_data_for_period['tap_venue_phone'], color: '#ff7891', fillOpacity: '0.8'},
        {label: 'Opening Hours', value: tap_data_for_period['tap_venue_opening'], color: '#ffa600', fillOpacity: '0.8'}
    ]);
    $("#num_donut_venue_tap_venue_website").html(tap_data_for_period['tap_venue_website']);
    $("#num_donut_venue_tap_venue_direction").html(tap_data_for_period['tap_venue_direction']);
    $("#num_donut_venue_tap_venue_phone").html(tap_data_for_period['tap_venue_phone']);
    $("#num_donut_venue_tap_venue_opening").html(tap_data_for_period['tap_venue_opening']);
}

function update_morris_donut_from(tap_data_for_period) {
    donut_from.setData([
        {
            label: 'Venues near by',
            value: tap_data_for_period['tap_from_venues_nearby'],
            color: '#57c7d4',
            fillOpacity: '0.8'
        },
        {label: 'Food', value: tap_data_for_period['tap_from_food'], color: '#f96197', fillOpacity: '0.8'},
        {label: 'Wine', value: tap_data_for_period['tap_from_wines'], color: '#926dde', fillOpacity: '0.8'},
        {label: 'Map', value: tap_data_for_period['tap_from_map'], color: '#eddcd5', fillOpacity: '0.8'}
    ]);
    $("#num_donut_from_tap_from_venues_nearby").html(tap_data_for_period['tap_from_venues_nearby']);
    $("#num_donut_from_tap_from_food").html(tap_data_for_period['tap_from_food']);
    $("#num_donut_from_tap_from_wines").html(tap_data_for_period['tap_from_wines']);
    $("#num_donut_from_tap_from_map").html(tap_data_for_period['tap_from_map']);
}


function init_morris_charts_venue(stats_for_year) {
    $(".custom-preloader").fadeOut('slow');
    chart_venue = Morris.Area({
        element: 'graph-taps-establishemnts',
//        data: [
//            {y: '2019-01', a: 24, b: 10, c: 6, d: 4},
//            {y: '2019-02', a: 20, b: 8, c: 4, d: 6},
//            {y: '2019-03', a: 22, b: 14, c: 5, d: 4},
//                {y: '2019-04', a: 20, b: 12, c: 4, d: 8},
//                {y: '2019-05', a: 20, b: 8, c: 4, d: 8},
//                {y: '2019-06', a: 20, b: 12, c: 4, d: 10},
//                {y: '2019-07', a: 22, b: 14, c: 5, d: 5},
//                {y: '2019-08', a: 22, b: 14, c: 5, d: 8}
//        ],
        data: stats_for_year['tap_venue_list'],
        lineColors: ['#55aff9', '#df91f1', '#ff7891', '#ffbc5e'],
        lineWidth: 0,
        resize: true,
        fillOpacity: 0.8,
        behaveLikeLine: true,
        gridLineColor: '#e0e0e0',
        hideHover: 'auto',
        pointSize: 1,
        gridTextSize: 11,
        xkey: 'y',
        ykeys: ['a', 'b', 'c', 'd'],
        labels: ['Website', 'Get Direction requests', 'Phone Calls', 'opening Hours'],
        resize: true,
        xLabels: "month",
        xLabelFormat: get_x_label_format, // function (x) { // <--- x.getMonth() returns valid index
        dateFormat: get_date_format
    });
}


function init_morris_charts_from(stats_for_year) {
    chart_from = Morris.Area({
        element: 'users-found-you',
        data: stats_for_year['tap_from_list'],
        lineColors: ['#57c7d4', '#f96197', '#926dde', '#eddcd5'],
        lineWidth: 0,
        resize: true,
        fillOpacity: 0.8,
        behaveLikeLine: true,
        gridLineColor: '#e0e0e0',
        hideHover: 'auto',
        pointSize: 1,
        gridTextSize: 11,
        xkey: 'y',
        ykeys: ['a', 'b', 'c', 'd'],
        labels: ['Venues near by', 'Food', 'Wine', 'Map'],
        resize: true,
        xLabels: "month",
        xLabelFormat: get_x_label_format,
        dateFormat: get_date_format
    });
}


function init_morris_donut_venue(donut_tap_data) {
    donut_venue = Morris.Donut({
        element: 'donut-taps-establishemnts',
        labelColor: '#9b9b9b',
        data: [
            {
                label: 'Website',
                value: donut_tap_data['this_month']['tap_venue_website'],
                color: '#55aff9',
                fillOpacity: '0.8'
            },
            {
                label: 'Get Direction',
                value: donut_tap_data['this_month']['tap_venue_direction'],
                color: '#df91f1',
                fillOpacity: '0.8'
            },
            {
                label: 'Phone Calls',
                value: donut_tap_data['this_month']['tap_venue_phone'],
                color: '#ff7891',
                fillOpacity: '0.8'
            },
            {
                label: 'Opening Hours',
                value: donut_tap_data['this_month']['tap_venue_opening'],
                color: '#ffa600',
                fillOpacity: '0.8'
            }
        ],
        formatter: function (y) {
            return y + " TAPS"
        }
    });
}


function init_morris_donut_from(donut_tap_data) {
    donut_from = Morris.Donut({
        element: 'where-users-came',
        labelColor: '#9b9b9b',
        data: [
            {
                label: 'Venues near by',
                value: donut_tap_data['this_month']['tap_from_venues_nearby'],
                color: '#57c7d4',
                fillOpacity: '0.8'
            },
            {label: 'Food', value: donut_tap_data['this_month']['tap_from_food'], color: '#f96197', fillOpacity: '0.8'},
            {
                label: 'Wine',
                value: donut_tap_data['this_month']['tap_from_wines'],
                color: '#926dde',
                fillOpacity: '0.8'
            },
            {label: 'Map', value: donut_tap_data['this_month']['tap_from_map'], color: '#eddcd5', fillOpacity: '0.8'}
        ],
        formatter: function (y) {
            return y + " TAPS"
        }
    });
}


function get_establishment_stats(url) {
    $.ajax({
        url: url,
        method: "GET",
        dataType: "json",
        success: function (data) {
            all_stats = data;
            year = 2020;  // TODO
            init_morris_charts_venue(all_stats['tap_stats_by_year'][year]);
            init_morris_charts_from(all_stats['tap_stats_by_year'][year]);
            init_morris_donut_venue(all_stats['donut_tap_data']);
            init_morris_donut_from(all_stats['donut_tap_data']);
        },
        error: function (xhr, status, error) {
            console.log(error);
        }
    })
}


app.ready(function () {
    get_establishment_stats(stats_url);
    change_remove_class_function();
    handle_wine_edit();
    handle_food_edit();
    wine_alerts(true);
    food_alerts(true);

    $("#year_venue").change(function () {
        var year = parseInt($(this).val());
        update_morris_chart_venue(all_stats['tap_stats_by_year'][year]);
    });
    $("#year_from").change(function () {
        var year = parseInt($(this).val());
        update_morris_chart_from(all_stats['tap_stats_by_year'][year]);
    });


    $("#donut_venue").change(function () {
        var period = $(this).val();
        update_morris_donut_venue(all_stats['donut_tap_data'][period]);
    });

    $("#donut_from").change(function () {
        var period = $(this).val();
        update_morris_donut_from(all_stats['donut_tap_data'][period]);
    });

    $('#post-edit').click(function (e) {
        validate_year_input(e);
        //TO BE CHECKED
        //validate_typeahead_inputs(e, wineNamesArray, winemakersArray, wineDomainArray);
    });

    $('#image-delete-food').click(function () {
        replace_food_image();
        $("#picture-removed-food").val("1");
    });

    $('#post-edit-food').click(function (e) {
        validate_add_food_inputs(e, "edit");
    });

    $('#post-delete').click(function (e) {
        e.preventDefault();
        $("#modal-default").modal('toggle');
        delete_data(event, "#edit-form2", "delete", "#qv-user-details", false, true);
    });

    $('#post-delete-food').click(function (e) {
        e.preventDefault();
        $("#modal-default").modal('toggle');
        delete_data(event, "#edit-form2", "delete", "#qv-user-details", false, true);
    });

});
