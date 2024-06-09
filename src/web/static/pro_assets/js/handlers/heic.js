function convert_heic(image_data, imageId, fallback) {
  var fd = new FormData();
  var files = image_data;
  fd.append('file', files);

  if (image_data.type != "image/heic") {
    $(imageId).attr('src', fallback);
    return;
  }

  $.ajax({
        url: '/ajax/convert-heic/',
        type: 'post',
        data: fd,
        contentType: false,
        processData: false,
        success: function(data) {
          $(imageId).attr('src', data['result']);
          return data;
        },
        error: function (xhr, status, error) {
            console.log(xhr.responseText, status, error);
            return []
        }
    });
}
