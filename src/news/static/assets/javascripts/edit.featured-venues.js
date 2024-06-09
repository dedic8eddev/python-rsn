function loadRelatedLists(){
  if (ajax_related_lists_url) {
    loadAndInsertHtmlByAjax(ajax_related_lists_url, "related_lists");
  }
}

init.push(function () {
    loadRelatedLists();
});


var pdg_widget = null;
var pdg_widget_language = null;
var pdg_widget_type = null;
init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
    pdg_widget_language = new PDG_Widget1({});
    pdg_widget_language.init();
    pdg_widget_type = new PDG_Widget2({});
    pdg_widget_type.init();
});



$(document).ready(function(){
  var all_places_by_ids = {};
  var publishStatus = $('input[name=status]');
  var connectedVenue = $('#id_connected_venue');
  var textStatus = $('button.btn.pdg-selected');

  $('#id_connected_venue').select2({
      allowClear: true,
      width: '100%',
      placeholder: 'Select Connected Venue...',

      dropdownParent: $('#connected_venue_selector'),
      ajax: {
          // url: "/ajax/autocomplete/place/published/list",
          url: "/ajax/autocomplete/place/for-featured-venue",

          dataType: 'json',
          delay: 250,
          processResults: function (data, params) {
              for (var i in data.items){
                  var item0 = data.items[i];
                  all_places_by_ids[item0.id] = item0;
              }
              params.page = params.page || 1;
              return {
                  results: $.map(data.items, function(item){
                      if (item.name){
                          item.text =  item.name + ", " + item.street_address + item.zip_code + item.city + item.country + item.type;
                          return item;
                      }
                  }),
              };
          },
      },
      cache: true,
  });

  $('#id_connected_venue').change(function(){
      $(".venueAction").removeClass("d-none")
  })

    $("#datetimepicker1").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $("#datetimepicker2").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $('#id_image_').on('change', function() {

      if (this.files[0].size > max_upload_size * 1000){
        if ($('.errorlist:contains("axim")').length < 2){
          $('#image_error_list').removeAttr('hidden');
        }
      } else {
        $('.errorlist:contains("axim")').attr('hidden', true);
      }

    });
    $('.limit-input').unbind('keyup change input paste').bind('keyup change input paste', function(e){
      var $this = $(this);
      var val = $this.val();
      var valLength = val.length;
      var maxCount = $this.attr('maxlength');
      counter = $(this).data('counter')
      lefter = $(this).data('left')

      localStorage.setItem(counter,valLength)
      localStorage.setItem(lefter,maxCount-valLength)

      $('#'+counter).text(valLength)
      $('#'+lefter).text(maxCount-valLength)
      if(valLength>maxCount){
          $this.val($this.val().substring(0,maxCount));
      }
  });
    var limit1 = $(".title_field").attr("maxlength");
    var limit2 = $(".description_field").attr("maxlength");
  
    if (!$(".description_field").val()) {
        $("#myCounter2").text("0")
        $("#left_limit2").text(limit2)

    }
    else{
        $("#left_limit2").text(localStorage.getItem("left_limit2"))
        $("#myCounter2").text(localStorage.getItem("myCounter2")-localStorage.getItem("left_limit2"))

    }
  
    if (!$(".title_field").val()) {
        $("#myCounter1").text("0")
        $("#left_limit1").text(limit1)
    }
    else{
        $("#left_limit1").text(localStorage.getItem("left_limit1"))
        $("#myCounter1").text(localStorage.getItem("myCounter1"))
    }

    if (publishStatus.val() == 20 && connectedVenue.val() === null) {
      $('.select2-container span.selection span.select2-selection').css('border', '2px solid red');
    }

    $('#placeform').submit(function (e) {
      if (connectedVenue.val() === null) {
          e.preventDefault();
      }
    });

    $('ul.dropdown-menu li a').click(function(){
      if(textStatus.attr('data-val') == 10 && connectedVenue.val() === null ){
        $('.select2-container span.selection span.select2-selection').css('border', '2px solid red');
      }else{
        $('.select2-container span.selection span.select2-selection').css('border', '1px solid #d6d6d6');
      }
    });

    connectedVenue.change(function(){
      if(textStatus.attr('data-val') == 20 && connectedVenue.val() === null ){
        $('.select2-container span.selection span.select2-selection').css('border', '2px solid red');
      }else{
        $('.select2-container span.selection span.select2-selection').css('border', '1px solid #d6d6d6');
      }
    });


});