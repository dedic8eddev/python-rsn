// ACTION: Initialize dropzone with custom settings
init_dropzones(establishmentLogoUrl, token, establishmentImagesUrl)

$(document).ready(function () {
  // ACTION: Get information about establishment and insert it into html body
  get_establishment_data(establishmentDataUrl)

  render_establishment_images(token, establishmentImagesUrl)
  update_sortable_view()
  wait_until_style_is_loaded()
  update_hours_css()

  // ACTION: Get information about establishment opening hours/holidays and insert it into html body
  get_hours_and_holidays(openingHoursUrl)

  $('input[id^=day]').each(function () {
    $(this).change(function () {
      validate_single_input(this);
      $('#error-message').remove();
      validate_hours(postEstablishmentHoursUrl);
    })
  })

  
    $('input[id^=day]').each(function () {
      $(this).keyup(function (event) {
        var thisInput = $(this);
        if (event.keyCode === 13) {
          validate_single_input(this);
          $('#error-message').remove();
          validate_hours(postEstablishmentHoursUrl);
          thisInput.blur(); 
          $(".clockpicker-popover").hide();
          $(".btn-delete-line").trigger("click")
        }
      })
    })


  $('#get_hours').change(function () {
    let inputElement = $('#input-file-now-custom-1')
    let element = inputElement.parent().find('.dropify-render').children()
    let imgSrc = element.length !== 0 ? element[0].src : ''
    let validated = validate_image(this)

    if (validated === 0) wait_until_logo_is_rendered(imgSrc)
    show_hide_dropify(1, this.value) //this.value stands for uploaded image, if there value is empty it means that on image upload user click on cancel button
  })

  $("[id^='opening-day']").on('change', function (e) {
    if (e.target.checked === false) {
      let errorMessage = $(this).parents().eq(3).find('#error-message')
      if (errorMessage.length !== 0) errorMessage.remove()
    }
  })

  // trigger post for closing open days
  $("[id^='switch-toggle']").on('click', function (e) {
    $("[id^='opening-day']").change(function () {
      if (!this.checked) {
        validate_hours(postEstablishmentHoursUrl)
      }
    })
  })

  $('#input-file-now-custom-2').change(function () {
    let inputElement = $('#input-file-now-custom-2')
    let element = inputElement.parent().find('.dropify-render').children()
    let imgSrc = element.length !== 0 ? element[0].src : ''
    let validated = validate_image(this, false)

    if (validated === 0) validate_image(this, true)
    wait_until_team_is_rendered(imgSrc)
    show_hide_dropify(5, this.value)
  })

  $('#input-file-now-custom-1').change(function () {
    let inputElement = $('#input-file-now-custom-1')
    let element = inputElement.parent().find('.dropify-render').children()
    let imgSrc = element.length !== 0 ? element[0].src : ''
    validate_image(this, false)

    wait_until_logo_is_rendered(imgSrc)
    show_hide_dropify(1, this.value)
  })

  $("[id^='add-hours-']").on('click', function () {
    setTimeout(function () {
      $('#error-message').remove()
      validate_hours(postEstablishmentHoursUrl)
    }, 50)
  })

  $(document.body).on('click', "[class*='btn-delete-holiday']", function () {
    setTimeout(function () {
      post_hours_and_holidays(postEstablishmentHoursUrl)
    }, 50)
  })

  $("[class*='btn-delete-']").on('click', function () {
    setTimeout(function () {
      $('#error-message').remove()
      validate_hours(postEstablishmentHoursUrl)
    }, 50)
  })

  $("[id^='holiday']").on('change', function () {
    setTimeout(function () {
      $('#error-message').remove()
      validate_hours(postEstablishmentHoursUrl)
    }, 50)
  })

  $("[id^='range']").on('change', function () {
    setTimeout(function () {
      $('#error-message').remove()
      validate_hours(postEstablishmentHoursUrl)
    }, 50)
  })

  anchor_handler()
})

// ACTON: On saving map, update phone number with selected dialCode
$(document).on('click', '#map-update', function () {
  let phoneNumberElement = $('#phone')
  if (!phoneNumberElement.val().startsWith('+')) {
    let dialCodeValue = window.intlTelInputGlobals.getInstance(
      phoneNumberElement[0]
    ).s.dialCode
    if (dialCodeValue)
      phoneNumberElement.val('+' + dialCodeValue + phoneNumberElement.val())
  }
})

$(document).on('input', '#input-file-now-custom-2', function () {
  let validated = validate_image(this, true)
  if (validated === 0) {
    updateLogo('team', $(this).value)
  }
})

$(document).on('input', '#input-file-now-custom-1', function () {
  let validated = validate_image(this, false)
  if (validated === 0) {
    updateLogo('place', $(this).value)
  }
})

$(document).on('dropify.afterClear', function (event, element) {
  let elementId = $(element)[0].element.id
  if (elementId === 'input-file-now-custom-1') {
    show_hide_dropify(1, false)
    removeLogo('place')
  }
  if (elementId === 'input-file-now-custom-2') {
    show_hide_dropify(5, false)
    removeLogo('team')
  }
  changed += 1
})

function removeLogo(logo_type) {
  $.ajax({
    url: postEstablishmentRemoveLogoUrl,
    headers: {
      'X-CSRFToken': token
    },
    type: 'post',
    async: false,
    dataType: 'json',
    data: { type: logo_type },
    error: function (xhr, status, error) {
      handle_sticky_save('error')
      console.log(error)
      return []
    }
  })
}

function updateLogo(logo_type, image_path) {
  var fd = new FormData()
  var sel =
    logo_type == 'place'
      ? '#input-file-now-custom-1'
      : '#input-file-now-custom-2'
  var files = $(sel)[0].files[0]
  fd.append('type', logo_type)
  fd.append('image', files)

  $.ajax({
    url: postEstablishmentUpdateLogoUrl,
    headers: {
      'X-CSRFToken': token
    },
    type: 'post',
    async: false,
    dataType: 'json',
    data: fd,
    contentType: false,
    processData: false,
    error: function (xhr, status, error) {
      handle_sticky_save('error')
      console.log(error)
      return []
    }
  })
}

function deleteImage(image_path) {
  $.ajax({
    url: postEstablishmentDeleteImgUrl,
    headers: {
      'X-CSRFToken': token
    },
    type: 'post',
    async: false,
    dataType: 'json',
    data: { image_path: image_path },
    error: function (xhr, status, error) {
      handle_sticky_save('error')
      console.log(error)
      return []
    }
  })
}

$(document).on('click', '.btn-show-hours', function () {
  let columnElements = $(this).parents().eq(2).children().eq(1).children()
  columnElements.each(function (index, element) {
    let className = $(element).attr('class').replace(' disabled', '')
    $(element).attr('class', className)
  })
})

app.ready(function () {
  $(document).off('click', '.img-item .btn-delete')

  // DELETION CLICKED IN SORTABLE
  $(document).on('click', '.img-item .btn-delete', function () {
    let parent_list = $(this)
      .parents('.sortable-row')
      .find('[data-provide="sortable"]')
    let parent_list_id = parent_list.attr('id').toLowerCase()

    let fullSrc = $(this).siblings('figure').children('img').attr('src')
    fullSrc = fullSrc.substring(fullSrc.indexOf('media/') + 6)
    fullSrc = fullSrc.replace('_tmb', '')

    deleteImage(fullSrc)
    $(this)
      .parents('.sortable-row')
      .find('[data-provide="sortable"]')
      .removeAttr('disabled')
    $(this).parents('.img-item').remove()

    show_hide_dropzone(parent_list_id)
    changed += 1
    return false
  })
})
