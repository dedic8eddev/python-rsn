init.push(function () {
    var places = [];

    var placesSource = new Bloodhound({
        datumTokenizer: Bloodhound.tokenizers.whitespace,
        queryTokenizer: Bloodhound.tokenizers.whitespace,
        dupDetector: function(a, b) { return a.id_str === b.id_str; },
        remote: {
            url: ajax_autocomplete_url,
            wildcard: '%QUERY',
            transform: function(response){
                return response.items;
            }
        },
        local: places
    });

    var empty = Handlebars.compile($("#typeahead-templates-empty-message").html());
    var suggestion = Handlebars.compile($("#typeahead-templates-suggestion").html());

    $("#id_geolocation").typeahead({
            hint: true,
            highlight: true,
            minLength: 1
        },
        {
            name: 'places',
            source: placesSource,
            displayKey: 'name',
            // display: 'value',
            templates: {
                empty: empty,
                suggestion: suggestion
            }

        }
    ).on("typeahead:selected", function(obj, datum){
        $("#id_place_id").val(datum.id);
        $("#geolocation_url").prop('href', datum.edit_url);
    });
});
