function loadRelatedLists(){
  if (ajax_related_lists_url) {
    loadAndInsertHtmlByAjax(ajax_related_lists_url, "related_lists");
  }
}

init.push(function () {
    loadRelatedLists();
});

var pdg_widget = null;

init.push(function () {
    pdg_widget = new PDG_Widget({});
    pdg_widget.init();
});

$(document).ready(function(){
    $("#datetimepicker1").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $("#datetimepicker2").flatpickr({
      enableTime: true,
      dateFormat: "Y-m-d H:i",
    });

    $('#id_image_event').on('change', function() {

      if (this.files[0].size > max_upload_size * 1000){
        if ($('.errorlist:contains("axim")').length < 2){
          $('#image_error_list').removeAttr('hidden');
        }
      } else {
        $('.errorlist:contains("axim")').attr('hidden', true);
      }

    });
});
