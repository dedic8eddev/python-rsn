// ---------------------------------- geolocation functions --------------------------------
// This example displays an address form, using the autocomplete feature
// of the Google Places API to help users fill in the information.

// This example requires the Places library. Include the libraries=places
// parameter when you first load the API. For example:
// <script src="https://maps.googleapis.com/maps/api/js?key=AIzaSyA2sCS5QpgQQOmMYtkWPR8-_8hXFJ8nDdk&libraries=places">

var user_location_share = false; // sharing user's own location

var placeSearch, autocomplete;

var other_fields_for_state = [];

var componentForm = {
    street_number: 'short_name',
    route: 'long_name',
    locality: 'long_name',
    administrative_area_level_1: 'short_name',
    administrative_area_level_2: 'long_name',
    country: 'long_name',
    postal_code: 'short_name'
};


function initAutocomplete() {
    // Create the autocomplete object, restricting the search to geographical
    // location types.
    autocomplete = new google.maps.places.Autocomplete(
        /** @type {!HTMLInputElement} */(document.getElementById('autocomplete')),
        {types: ['geocode']});

    // When the user selects an address from the dropdown, populate the address
    // fields in the form.
    autocomplete.addListener('place_changed', fillInAddress);
    $("#id_full_street_address").val("");
    $("#route").change(function(){
        $("#id_full_street_address").val($(this).val());
        $("#id_street_address").val($(this).val());
    });

//    $("#street_number").change(function(){
//        $("#id_house_number").val($(this).val());
//    });

    $("#locality").change(function(){
        $("#id_city").val($(this).val());
    });

    $("#administrative_area_level_1").change(function(){
        var this_val = $(this).val();

        $("#id_state").val(this_val);

        if (other_fields_for_state.length > 0){
            for (var i in other_fields_for_state) {
                var id_field = "#"+other_fields_for_state[i];
                $(id_field).val(this_val);
            }
        }

    });
    $("#country").change(function(){
        $("#id_country").val($(this).val());
    });

    $("#postal_code").change(function(){
        $("#id_zip_code").val($(this).val());
    });
}

function initAutocompleteJp() {
    // Create the autocomplete object, restricting the search to geographical
    // location types.
    autocomplete_jp = new google.maps.places.Autocomplete(
        /** @type {!HTMLInputElement} */(document.getElementById('autocomplete-jp')),
        {
            types: ['geocode', 'establishment'],
            'componentRestrictions': {country: 'jp'}
        });

    // When the user selects an address from the dropdown, populate the address
    // fields in the form.
    autocomplete_jp.addListener('place_changed', fillInAddressJp);
}

$(document).ready(function (){
    $('#id_district').change(function () {
        $('#id_new_district_name').attr('type', 'hidden')
        if ($('#id_district option:selected').val() == '') {
            $('#id_new_district_name').val('')
        }
        else {
            $('#id_new_district_name').val($('#id_district option:selected').text())
        }

    })
    $('#locality').on('keyup change', function () {
        get_django_citites_data()
    })
})

function fillInAddress() {
    // Get the place details from the autocomplete object.
    var place = autocomplete.getPlace();
    $("#autocomplete-jp").val("");

    fillInAddressCommon(place);
}


function fillInAddressJp() {
    // Get the place details from the autocomplete object.
    var place = autocomplete_jp.getPlace();

    $("#autocomplete").val("");

    setMapLocationCommon(place);

    $.ajax({
        type        : "POST",
        url         : "/ajax/autocomplete/address/place_id",
        dataType    : 'json',
        data        : {
            'place_id': place.place_id,
            'lang': 'ja'
        },
        success: function(data) {
            if(data.full_street_address) {
                var dr_route = data.full_street_address;
            }else if(data.route) {
                var dr_route = data.route;
            } else {
                var dr_route = "";
            }

            if(data.city) {
                var dr_locality = data.city;
            } else {
                var dr_locality = "";
            }

            if(data.state) {
                var dr_state = data.state;
            } else {
                var dr_state  = "";
            }

            if(data.postal_code) {
                var dr_postal_code = data.postal_code;
            } else {
                var dr_postal_code  = "";
            }

            if(data.country) {
                var dr_country = data.country;
            } else {
                var dr_country  = "";
            }

            if(data.iso) {
                var dr_iso = data.iso;
            } else {
                var dr_iso  = "";
            }

            $("#route").val(dr_route);
            $("#id_full_street_address").val(dr_route);
            $("#id_street_address").val(dr_route);
            $("#id_house_number").val("");

            $("#locality").val(dr_locality);
            $("#id_city").val(dr_locality);

            $("#administrative_area_level_1").val(dr_state);
            $("#id_state").val(dr_state);

            $("#postal_code").val(dr_postal_code);
            $("#id_zip_code").val(dr_postal_code);

            $("#country").val(dr_country);
            $("#id_country").val(dr_country);

            $("#id_country_iso_code").val(dr_iso);
        },
        error: function(data){
            console.warn(data);
        }
    });

}


function setMapLocationCommon(place) {
    $("#id_latitude").val(place.geometry.location.lat());
    $("#id_longitude").val(place.geometry.location.lng());

    $("#id_pin_latitude").val(place.geometry.location.lat());
    $("#id_pin_longitude").val(place.geometry.location.lng());

    var new_position = new google.maps.LatLng(place.geometry.location.lat(), place.geometry.location.lng());

    // calling map
    marker.position = new_position;
    map.setCenter(marker.position);
    marker.setPosition(new_position);
    marker.setMap(map);
}


function get_django_citites_data () {
    url = '/api/search_city/'//?city=Massandra&lat=36.3020023&lng=-88.32671069999999
    data_search = {
        'city': $('#locality').val(),
        'lat': $("#id_latitude").val(),
        'lng': $("#id_longitude").val()
    }
    $.ajax(
        {
            type: "GET",
            url: url,
            dataType: 'json',
            data: data_search,
            success: function (data) {
                $('#id_new_city').val(data.city.id)
                $('#id_new_city_name').val(data.city.name)
                $('#id_new_district_name').attr('type', 'hidden')
                $('#id_new_district_name').val('')
                var $select = $('#id_district');
                $select.find('option').remove();
                $select.append('<option value="">' + '--No District--' + '</option>');
                $.each(data.districts, function (district) {
                    var d = data.districts[district]
                    $select.append('<option value=' + d.id + '>' + d.name + '</option>'); // return empty
                });
                $('.city_will_be_created').hide()
            },
            error: function (data) {
                $('#id_new_city').val('')
                $('#id_new_city_name').val('')
                $('#id_new_district_name').attr('type', 'hidden')
                $('#id_new_district_name').val('')
                var $select = $('#id_district');
                $select.find('option').remove();
                $select.append('<option value="">' + '--No District--' + '</option>');
                console.log(data_search.city.length)
                if (data_search.city.length > 0) {
                    $('.city_will_be_created').show()
                } else {
                    $('.city_will_be_created').hide()
                }


            }
        },
    )
}

function fillInAddressCommon(place) {
    setMapLocationCommon(place);

    for (var component in componentForm) {
        if ($("#"+component).length > 0) {
            $("#"+component).val('');
            $("#"+component).prop('disabled', false)
        }
    }

    // Get each component of the address from the place details
    // and fill the corresponding field on the form.
    var complete_addr = {}
    var sublocalities = {};
    var country_iso_code = '';

    // Nakahiro, 2, Ako, Hyogo Prefecture 678-0232, Japan
    for (var i = 0; i < place.address_components.length; i++) {
        var addressType = place.address_components[i].types[0];

        if (componentForm[addressType]) {
            var val = place.address_components[i][componentForm[addressType]];
            var hidden_id = null;
            complete_addr[addressType] = val;

            if (addressType=='country'){
                country_iso_code = place.address_components[i]['short_name'];
            }
        } else {
            if (addressType.search('sublocality_level_') >= 0){
                var val = place.address_components[i]['long_name'];
                var sub_level = addressType.substr(18);
                sublocalities[sub_level] = val;
            }
        }
    }

    if(complete_addr['route'] != undefined && complete_addr['route'] != '') {
        var val = complete_addr['route'];
        hidden_id = 'id_street_address';
        $("#"+hidden_id).val(val);
    }else if ((Object.keys(sublocalities).length > 0) && (country_iso_code == 'JP')){
        sub_val_out = [];
        hidden_id = 'id_street_address';

        var keys_x = Object.keys(sublocalities).sort();
        for (var ki in keys_x) {
            var key_x = keys_x[ki];
            var sub_val_item = sublocalities[key_x];
            sub_val_out.push(sub_val_item);
        }

        $("#"+hidden_id).val(sub_val_out.join(', '));
    }


    if(complete_addr['street_number'] != undefined && complete_addr['street_number'] !='') {
        var val = complete_addr['street_number'];
        hidden_id = 'id_house_number';
        $("#"+hidden_id).val(val);
    }

    if(complete_addr['locality'] != undefined && complete_addr['locality'] !='') {
        var val = complete_addr['locality'];
        hidden_id = 'id_city';
        $("#locality").val(val);
        $("#"+hidden_id).val(val);
    } else if(complete_addr['administrative_area_level_2'] != undefined &&
            complete_addr['administrative_area_level_2'] !='') {
        var val = complete_addr['administrative_area_level_2'];
        hidden_id = 'id_city';
        $("#locality").val(val);
        $("#"+hidden_id).val(val);
    }

    if(complete_addr['administrative_area_level_1'] != undefined &&
            complete_addr['administrative_area_level_1'] !='') {
        var val = complete_addr['administrative_area_level_1'];
        hidden_id = 'id_state';
        $("#administrative_area_level_1").val(val);
        $("#"+hidden_id).val(val);

        if (other_fields_for_state.length > 0){
            for (var i in other_fields_for_state) {
                var id_field = "#"+other_fields_for_state[i];
                $(id_field).val(val);
            }
        }

    }

    if(complete_addr['country'] != undefined && complete_addr['country'] !='') {
        var val = complete_addr['country'];
        hidden_id = 'id_country';
        $("#country").val(val);
        $("#"+hidden_id).val(val);
    }

    if(complete_addr['postal_code'] != undefined && complete_addr['postal_code'] !='') {
        var val = complete_addr['postal_code'];
        hidden_id = 'id_zip_code';
        $("#postal_code").val(val);
        $("#"+hidden_id).val(val);
    }

    if(place.name) {
        var val = place.name;

        if(complete_addr['locality'] != undefined && complete_addr['locality'] != null &&
                complete_addr['locality'] != ''){
            if(complete_addr['locality'] != val) {
                $("#route").val(val);
                $("#id_full_street_address").val(val);
                $("#id_street_address").val(val);
            }
        }else{
            $("#route").val(val);
            $("#id_full_street_address").val(val);
            $("#id_street_address").val(val);
        }
    }

    get_django_citites_data()
}



// Bias the autocomplete object to the user's geographical location,
// as supplied by the browser's 'navigator.geolocation' object.

function geolocate() {
    if($("#user_location_share").prop('checked')){
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(function(position) {
                var geolocation = {
                    lat: position.coords.latitude,
                    lng: position.coords.longitude
                };
                var circle = new google.maps.Circle({
                    center: geolocation,
                    radius: position.coords.accuracy
                });
                autocomplete.setBounds(circle.getBounds());
            });
        }
    }
}

// ---------------------------------- /geolocation functions --------------------------------
