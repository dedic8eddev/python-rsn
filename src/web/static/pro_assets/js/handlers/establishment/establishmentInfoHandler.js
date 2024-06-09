$('#infos').find(':input').each(function(){
  add_change_listener($(this));
});

$('#establishment_map_form').find(':input').each(function(){
  add_change_listener($(this));
});

function add_change_listener(element) {
    $(element).on('change', function (e) {
        post_establishment_info_data(e);
    });
}

// Checks if at least one checkbox in ESTABLISHMENT INFO is selected
function checkboxes_are_valid() {
    let checked = $(".custom-control-input:checked");
    let errorMessage = $("#type-error");
    if (checked.length < 1) {
        errorMessage.show()
        return false;
    } else {
        errorMessage.hide();
        return true;
    }
}

function post_establishment_info_data(e){


  if (window.location.href.includes('infos')){
    form = $('#infos');
    if (!checkboxes_are_valid()){
      return;
    }
  } else if (window.location.href.includes('map')){
    form = $('#establishment_map_form')
  }
  data = form.serializeArray();

  $.ajax({
      url: postEstablishmentInfoUrl,
      headers: {
          'X-CSRFToken': token
      },
      type: 'post',
      dataType: 'json',
      data: data,
      error: function (xhr, status, error) {
        handle_sticky_save('error');
        console.log(error);
      },
  });
}
