// --------------------------------- map related functions --------------------------------

var map = null;
var marker = null;

function initMap() {
    var lat_default = 48.8588376;  // Paris itself
    var lng_default = 2.2773452;   // Paris itself

    var lat_form = $("#pin_latitude").val();
    var lng_form = $("#pin_longitude").val();

    if(lat_form != undefined && lat_form != null && lat_form != '' &&
        lng_form != undefined && lng_form != null && lng_form != ''){
        current_lat = parseFloat(lat_form);
        current_lng = parseFloat(lng_form);
    }else{
        current_lat = parseFloat(lat_default);
        current_lng = parseFloat(lng_default);
    }

    var current_lat_lng = new google.maps.LatLng(current_lat, current_lng);

    map = new google.maps.Map(document.getElementById('map'), {
        center: {lat: current_lat, lng: current_lng},
        zoom: 13
    });

    marker = new google.maps.Marker({
        map: map,
        draggable:true,
        anchorPoint: new google.maps.Point(0, -29),
        position: current_lat_lng
    });

    map.setCenter(marker.position);
    marker.setMap(map);

}
