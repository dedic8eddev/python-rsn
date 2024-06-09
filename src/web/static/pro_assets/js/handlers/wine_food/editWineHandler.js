function wine_data(element, wine) {
  let image_src = element.getElementsByTagName('img').item(0).src
  let post_id = element.name
  let wineYear = wine.year === '0' ? '' : wine.year

  return {
    id: wine.id,
    post_id: post_id,
    name: wine.name,
    winemakers: wine.winemakers,
    domain: wine.domain,
    color: wine.color,
    is_sparkling: wine.is_sparkling,
    comment: wine.comment,
    image:
      '<img class="w-130px rounded" id="wine-image" src="' +
      image_src +
      '" alt="VN (red)">',
    //        "year": "<input type=\"number\" min=\"1000\" max=\"2099\" class=\"form-control\"  id=\"wine-year-id\" name=\"wineYear\" value=\"" + wineYear + "\"><label>Vintage</label>",
    year: wineYear,
    //        "grape_variety": "<input type=\"text\" class=\"form-control\"  name=\"wineGrapeVariety\" value=\"" + wine.grape_variety + "\"><label>Grape Variety</label>"
    grape_variety: wine.grape_variety,
    price: wine.price
  }
}

const disabledModeratedFields =
  '#edit-form #n-ame-typeahead'


const readonlyModeratedFields =
  '#edit-form select, button[name=edit-wine-image], button[id=image-delete], button[data-id=wineColor], #edit-form input:not([name=wine-price], [name=wineYear], [type=hidden])'

function readonlyModerateEditing() {
  $(readonlyModeratedFields).prop('readonly', true).css({
    'margin-top': '10px',
    'padding-left': '7px',
    border: 'none',
    background:
      'center right 7px no-repeat url(/static/pro_assets/img/lock.svg)',
    'background-size': '15px',
    'background-color': '#eee'
  })

  $('button[id=image-delete]').css({
    'text-indent': '-9999px',
    width: '31px',
  })

  $('button[name=edit-wine-image]').css({
    width: '163px',
  })

}

function disabledModerateEditing() {
  $(disabledModeratedFields).prop('disabled', true)
  if ($(disabledModeratedFields).parent().next().attr('class') != 'select_lock'){
    $(disabledModeratedFields).parent().after('<div class="select_lock" style="background: url(/static/pro_assets/img/lock.svg) 80% 80% no-repeat; background-size: contain; width: 16px; height: 24px"></div>')
    let width = parseInt($(disabledModeratedFields).next().css('width').replaceAll('px', '')) - 20
    $(disabledModeratedFields).next().css('width', width)
  }
  $('button[name=edit-wine-image], button[id=image-delete], button[data-id=wineColor]').prop('disabled', true)
  $('button#post-edit').prop('disabled', true)
  $('#edit-form input[name=wine-price], [name=wineYear], [type=hidden]').on('input', function () {
        $('button#post-edit').prop('disabled', false)
    })
}

function enableModerateEditing() {
  $(readonlyModeratedFields).prop('readonly', false).removeAttr('style')
  $(disabledModeratedFields).prop('disabled', false).removeAttr('style')
  if ($(disabledModeratedFields).parent().next().attr('class') == 'select_lock'){
    $(disabledModeratedFields).parent().next().remove()
    let width = parseInt($(disabledModeratedFields).next().css('width').replaceAll('px', '')) + 20
    $(disabledModeratedFields).next().css('width', width)
  }
}

function render_edit_wine_view(element, reverseUrl) {
  const moderatedStatus = ['natural', 'organic', 'doubt', 'conventional']
  let wineId = element.id
  let postId = element.name
  let wineStatus = $(element).attr('status')

  if (!moderatedStatus.includes(wineStatus)) {
    enableModerateEditing()
  }

  $.ajax({
    url: reverseUrl.replace(/12345/, postId.toString()),
    method: 'GET',
    success: function (data) {
      data.result.id = wineId
      data.result.postId = postId
      insert_wine_input_data(data.result.color, data.result.is_sparkling)
      update_wine_modal(element, data.result)
      if (!data.result.all_editable && moderatedStatus.includes(wineStatus)){
        disabledModerateEditing()
        readonlyModerateEditing()
      }
    },
    error: function (xhr, status, error) {
      alert(error)
    }
  })
}

function update_wine_modal(element, data) {
  let wine = wine_data(element, data)
  select_wine_color(wine.color)

  set_do_float_wine()

  let checkbox = $('input[type="checkbox"]')
  wine.is_sparkling === true
    ? checkbox.prop('checked', true)
    : checkbox.prop('checked', false)

  $('#n-ame-typeahead').val(wine.name)
  $('#select2-n-ame-typeahead-container').trigger('change')
  $('#winemakers-typeahead').val(wine.winemakers)
  $('#domain-typeahead').val(wine.domain)
  $('#wine-comment-input').val(wine.comment)
  $('#wine-price').val(wine.price)

  $('#wine-id').val(wine.id).attr('readonly', true)
  $('#post-id').val(wine.post_id).attr('readonly', true)
  $('#post-id-delete').val(wine.post_id).attr('readonly', true)
  $('#wine-img-container').html(wine.image)
  $('#wine-year-id').val(wine.year)

  $('#wine-year-id').bind('keyup mouseup', function () {
    changed += 1
  })
  //    $("#wine-grape-variety").html(wine.grape_variety);
  $('#wine-grape-variety-id').val(wine.grape_variety)
}

function select_wine_color(colorValue) {
  let colorSelect = '#wineColor'

  $(colorSelect).val(colorValue.toString())
  $(colorSelect).selectpicker('refresh')
}

// Prevents edit input fields to be obscured by its parent
function set_do_float_wine() {
  $('#n-ame-typeahead').parents().eq(3).addClass('form-group do-float')
  $('#winemakers-typeahead').parents().eq(3).addClass('form-group do-float')
  $('#domain-typeahead').parents().eq(3).addClass('form-group do-float')
  $('#wine-year').parents().eq(3).addClass('form-group do-float')
  $('#wine-comment-input').parents().eq(3).addClass('form-group do-float')
}

function insert_wine_input_data(color, sparkling) {
  $('#wine-color-input').val(color)
  $('#wine-sparkling-input').val(sparkling)
}

function wait_until_list_is_displayed() {
  let typeahead = $('#typeahead-name').find('.typeahead__result')
  let list_elements = typeahead.find('ul').find('li')
  if (list_elements.length === 0)
    return setTimeout(wait_until_list_is_displayed, 10)
  list_elements.each(function (index, element) {
    let imgElement = $(element).find('img')
    let src = imgElement.attr('src')
    // imgElement.attr('src', src.replace('</strong>', ''))
    if (src.includes('none')) imgElement.remove()
  })
}
function handle_wine_edit() {
  $('a[href="#qv-user-details"]').click(function () {
    removeHash()
    wine_change_listener('')
    clear_image_input('edit', true)
    clear_edit_comment_input()
    hide_errors()
    render_edit_wine_view(this, winePostUrl)
  })

  // ACTION: Click on delete image button
  $(document).on('click', '#image-delete', function () {
    clear_image_input('edit', true)
    replace_wine_image()
  })

  // ACTION: Adding image in edit wine modal
  $('input[id="modify-image-edit"]').change(function () {
    upload_image(this, 'wine', 'edit')
  })


  // ACTION: Load active winemakers to typeahead data
  $.typeahead({
    input: '.form-control.winemakers-typeahead',
    order: 'desc',
    source: {
      data: winemakersArray
    },
    callback: {
      onClickAfter: function (node, a, item, e) {
        add = ''
        if (node[0].id.includes('add')) {
          add = '-add'
        }
        complete_domain_name(item.display, add)
      }
    }
  })

  // ACTION: Load active wine domains to typeahead data
  $.typeahead({
    input: '.form-control.domain-typeahead',
    order: 'desc',
    source: {
      data: wineDomainArray
    }
  })
}

function complete_domain_name(winemaker_name, add) {
  $.ajax({
    url: domain_url,
    type: 'get',
    async: false,
    dataType: 'json',
    data: { winemaker: winemaker_name },
    success: function (data) {
      update_domain_name(data, add)
    },
    error: function (xhr, status, error) {
      console.log(error)
    }
  })
}
