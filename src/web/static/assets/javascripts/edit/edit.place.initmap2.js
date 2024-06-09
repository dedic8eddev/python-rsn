// --------------------------------- map related functions --------------------------------

var map = null;
var marker = null;

function initMap() {
    var lat_default = 48.8588376;  // Paris itself
    var lng_default = 2.2773452;   // Paris itself

    var lat_form = $("#id_pin_latitude").val();
    var lng_form = $("#id_pin_longitude").val();

    if(lat_form != undefined && lat_form != null && lat_form != '' &&
        lng_form != undefined && lng_form != null && lng_form != ''){
        current_lat = parseFloat(lat_form);
        current_lng = parseFloat(lng_form);
    }else{
        current_lat = parseFloat(lat_default);
        current_lng = parseFloat(lng_default);
    }

    var current_lat_lng = new google.maps.LatLng(current_lat, current_lng);

    

    var googleMap = document.getElementsByClassName("map");

    for (var i = 0; i < googleMap.length; i++) {
        map = new google.maps.Map(googleMap[i], {
          center: {lat: current_lat, lng: current_lng},
          zoom: 13
    });
    


    var input = /** @type {!HTMLInputElement} */(
        document.getElementById('pac-input'));

    var types = document.getElementById('type-selector');
    map.controls[google.maps.ControlPosition.TOP_LEFT].push(input);
    map.controls[google.maps.ControlPosition.TOP_LEFT].push(types);

    var autocomplete = new google.maps.places.Autocomplete(input);
    autocomplete.bindTo('bounds', map);

    var infowindow = new google.maps.InfoWindow();

    marker = new google.maps.Marker({
        map: map,
        draggable:true,
        anchorPoint: new google.maps.Point(0, -29),
        position: current_lat_lng
    });

    google.maps.event.addListener(marker, 'dragend', function(evt){
        var new_lat = evt.latLng.lat();
        var new_lng = evt.latLng.lng();

        map.setCenter(marker.position);
        marker.setMap(map);

        $("#id_pin_latitude").val(new_lat);
        $("#id_pin_longitude").val(new_lng);
    });

    google.maps.event.addListener(marker, 'dragstart', function(evt){
    });

    

    autocomplete.addListener('place_changed', function() {
      infowindow.close();
      marker.setVisible(false);
      var place = autocomplete.getPlace();
      if (!place.geometry) {
        window.alert("Autocomplete's returned place contains no geometry");
        return;
      }

      // If the place has a geometry, then present it on a map.
      if (place.geometry.viewport) {
        map.fitBounds(place.geometry.viewport);
      } else {
        map.setCenter(place.geometry.location);
        map.setZoom(17);  // Why 17? Because it looks good.
      }
      marker.setIcon(/** @type {google.maps.Icon} */({
        url: place.icon,
        size: new google.maps.Size(71, 71),
        origin: new google.maps.Point(0, 0),
        anchor: new google.maps.Point(17, 34),
        scaledSize: new google.maps.Size(35, 35)
      }));
      marker.setPosition(place.geometry.location);
      marker.setVisible(true);

      var address = '';
      if (place.address_components) {
        address = [
          (place.address_components[0] && place.address_components[0].short_name || ''),
          (place.address_components[1] && place.address_components[1].short_name || ''),
          (place.address_components[2] && place.address_components[2].short_name || '')
        ].join(' ');
      }

        $("#id_latitude").val(place.geometry.location.lat());
        $("#id_longitude").val(place.geometry.location.lng());

        $("#id_pin_latitude").val(place.geometry.location.lat());
        $("#id_pin_longitude").val(place.geometry.location.lng());

      infowindow.setContent('<div><strong>' + place.name + '</strong><br>' + address);
      infowindow.open(map, marker);
    });

    // Sets a listener on a radio button to change the filter type on Places
    // Autocomplete.
    function setupClickListener(id, types) {
      var radioButton = document.getElementById(id);
      radioButton.addEventListener('click', function() {
        autocomplete.setTypes(types);
      });
    }

    setupClickListener('changetype-all', []);
    setupClickListener('changetype-address', ['address']);
    setupClickListener('changetype-establishment', ['establishment']);
    setupClickListener('changetype-geocode', ['geocode']);

    initAutocomplete();
    initAutocompleteJp();
  }
}
// --------------------------------- /map related functions --------------------------------
