function post_hours_and_holidays(url) {
  let hours = generate_establishment_data_json()
  $.ajax({
    url: url,
    method: 'POST',
    contentType: 'application/json',
    dataType: 'json',
    data: hours,
    error: function () {
      handle_sticky_save('error')
    }
  })
}
function get_hours_and_holidays(url) {
  $.ajax({
    url: url,
    method: 'GET',
    success: function (data) {
      let holidays = get_holidays_dates(data)
      let dateRange = get_holidays_dateRange(data)
      render_establishment_hours(data)
      render_holidays(holidays);   
      render_holidaysRange(dateRange)
    },
    error: function (xhr, status, error) {
      console.log(error)
    }
  })
}

// -------------------------------------------------- HOURS -------------------------------------------------- //

function render_establishment_hours(data) {
  delete data.holidays
  delete data.date_range
  for (const property in data) {
    let active = data[property].active
    let addHours = data[property].add_hours
    let hours = data[property].hours

    let activeInput = $(active[0])
    let divs = get_divs_to_be_customized(activeInput)
    if (active[1]) {
      if (!activeInput.is(':checked')) {
        activeInput.click()
        divs_enable_disable(divs)
      }
      let hourFrom = hours[0]
      let hourTo = hours[1]

      $(hourFrom[0]).val(hourFrom[1])
      $(hourTo[0]).val(hourTo[1])

      if (hours.length > 2) {
        hourFrom = hours[2]
        hourTo = hours[3]
        $(hourFrom[0]).val(hourFrom[1])
        $(hourTo[0]).val(hourTo[1])
        enable_second_hour_row(addHours)
      }
      divs_enable_disable(divs, false)
    } else {
      if (activeInput.is(':checked')) {
        activeInput.click()
        divs_enable_disable(divs, true)
      }
    }
  }
}

// Converts opening hours and holidays to JSON accepted by the backend
function generate_establishment_data_json() {
  let response = {}

  for (let i = 1; i <= 7; i++) {
    response[i] = get_hours(i)
  }
  response['holidays'] = get_holidays()
  return JSON.stringify(response)
}

function enable_second_hour_row(element) {
  let addHours = $(element)
  let disabledRow = addHours.parents().eq(1).next()

  let addHoursClassName = addHours.attr('class')
  let disableRowClassName = disabledRow.attr('class')

  addHoursClassName += ' disabled'
  disableRowClassName = disableRowClassName.replace(' disabled', '')

  addHours.attr('class', addHoursClassName)
  disabledRow.attr('class', disableRowClassName)
  disabledRow.children().each(function (index, element) {
    $(element).attr('class', element.className.replace(' disabled', ''))
  })
}

function get_hours(switchNum) {
  let switchId = '#switch-' + switchNum

  if (!is_opened(switchId)) {
    return []
  }

  let container = $(switchId).parents().eq(2).children()
  let hourColumn1 = container[0]
  let hourColumn2 = container[1]

  let resultColumn1 = get_hour_input_values(hourColumn1)[0]

  let resultColumn2 = []
  if (is_column_active(hourColumn2)) {
    resultColumn2 = get_hour_input_values(hourColumn2, true)[0]
  }

  return [resultColumn1, resultColumn2]
}

function get_hour_input_values(element, second = false) {
  
  let hourFromIndex = 1
  let hourToIndex = 2

  if (second) {
    hourFromIndex--
    hourToIndex--
  }

  let hourFromElement = element.children[hourFromIndex].getElementsByTagName(
    'input'
  )[0]
  let hourFromTo = element.children[hourToIndex].getElementsByTagName(
    'input'
  )[0]

  return [
    [
      hourFromElement.value.replace('24:', '00:'),
      hourFromTo.value.replace('00:00', '23:59')
    ],
    [hourFromElement, hourFromTo]
  ]
}

// -------------------------------------------------- HOLIDAYS -------------------------------------------------- //

function render_holidays(holidays) {
  let holidayId = '#holiday'
  let closedId = '#closed-holiday'
  $(holidayId).val(holidays[0]);
  $(closedId).prop('checked', true);
  for (let i = 1; i < holidays.length; i++) {
    generate_holiday_element(holidayId, closedId, holidays[i], i);
  }
}

function render_holidaysRange(date_range) {
  let holidayRangeId = '#date-range'
  let closedRangeId = '#closed-date-range'
  $(closedRangeId).prop('checked', true);
  $(holidayRangeId).find('.start-date').val(date_range[0].slice(0, 10))
  $(holidayRangeId).find('.end-date').val(date_range[0].slice(-10))
  for (let i = 1; i < date_range.length; i++) {
    generate_holiday_range_element(holidayRangeId,closedRangeId,date_range[i].slice(0, 10),date_range[i].slice(-10), i);
  }
}

function generate_holiday_element(holidayId, closedId, holidayDate, iter) {
  let holidaysListItem = $('#holidays-list .time-item')
  let index = holidaysListItem.length + 1
  let html = holidaysListItem.eq(0).html()
  let searchStr = 'holiday'
  let replaceStr = 'holiday' + index

  let idEnding = iter + 1
  holidayId += idEnding
  closedId += idEnding

  let divIndex = html.lastIndexOf('</div>')
  html =
    html.substring(0, divIndex) +
    '<button class="btn btn-link btn-delete-holiday"><i class="ti-close"></i></button></div>';

  html =
    '<div class="form-group time-item d-block">' +
    replaceAll(searchStr, replaceStr, html) +
    '</div>'
  $('#holidays-list').append(html)
  $(holidayId).val(holidayDate)
  $(closedId).prop('checked', true)
}

function generate_holiday_range_element(holidayId, closedId, holidayStartDate,holidayEndtDate, iter) {
  let holidaysRangeListItem = $('#holidays-list-range .time-item')
  let indexRange = holidaysRangeListItem.length + 1
  let htmlRange = holidaysRangeListItem.eq(0).html()
  let searchStrRange = 'date-range'
  let replaceStrRange = 'date-range' + indexRange

  let idEndingRange = iter + 1
  holidayId += idEndingRange
  closedId += idEndingRange

  let divIndexRange = htmlRange.lastIndexOf('</div>')
  htmlRange =
    htmlRange.substring(0, divIndexRange) +
    '<button class="btn btn-link btn-delete-holiday"><i class="ti-close"></i></button></div>';

  htmlRange =
    '<div class="form-group time-item">' +
    replaceAll(searchStrRange, replaceStrRange, htmlRange) +
    '</div>'
  $('#holidays-list-range').append(htmlRange)
  $(holidayId).find('.start-date').val(holidayStartDate)
  $(holidayId).find('.end-date').val(holidayEndtDate)
  $(closedId).prop('checked', true)
}

function get_holidays() {
  let holidays = []

  $('input[id^="holiday"]').each(function () {
    if (this.value) holidays.push(this.value)
  })
  $('div[id^="date-range"]').each(function () {
    var rangeStart = $(this).find('.start-date').val();    
    var rangeEnd = $(this).find(".end-date").val();
    if (rangeStart && rangeEnd) holidays.push(rangeStart + "-" + rangeEnd)
  })
  return holidays
}

function get_holidays_dates(data) {
  let holidays = data.holidays
  delete data.holidays
  return holidays
}
function get_holidays_dateRange(data) {
  let dateRange = data.date_range
  delete data.dateRange
  return dateRange
}

// -------------------------------------------------- VALIDATORS -------------------------------------------------- //

// Core validator, which triggers all HOUR validators on SAVE CHANGES button click
function validate_hours(url) {
  let switchId
  let cancel = 0

  for (let i = 1; i <= 7; i++) {
    switchId = '#switch-' + i
    if (is_opened(switchId)) {
      let container = $(switchId).parents().eq(2).children()
      let hourColumn1 = container[0]
      let hourColumn2 = container[1]

      cancel += input_error_handler(hourColumn1)
      //if validation is needed // ex. 13:00 - 12:00 -> ERROR
      cancel += validate_hour_input(hourColumn1);

      if (is_column_active(hourColumn2)) {
        cancel += input_error_handler(hourColumn2, true)
        cancel += validate_hour_rows(hourColumn1, hourColumn2)
      }else{
        cancel += validate_hour_input(hourColumn1)
      }
    }
  }
  if (cancel === 0) post_hours_and_holidays(url)
}

// Checks if OPENING HOURS ROW1 overlaps OPENING HOURS ROW2
// ROW1: 08:00 - 16:00 ROW2: 14:00 - 19:00 -> ERROR
function validate_hour_rows(element1, element2) {
  let cancel = 0
  cancel += validate_hour_input(element1)
  cancel += validate_hour_input(element2, true)

  if (cancel !== 0) return cancel

  let container = get_hour_input_values(element1)

  let elements = container[1]
  let hoursContainer1 = container[0]
  let hoursContainer2 = get_hour_input_values(element2, true)[0]

  if (hoursContainer2[0] < hoursContainer1[1]) {
    //let errorMessage = 'Opening Hour Overlaps Closing Hour!';

    let errorMessage;
    if(language === "FR"){
      errorMessage = "Les horaires d'ouverture coïncident avec les horaires de fermeture !";
    }
    else if(language === "IT"){
      errorMessage = "L'orario di apertura si sovrappone all'orario di chiusura!";
    }
    else{
      errorMessage = 'Opening Hour Overlaps Closing Hour!';
    }
    render_error_message(errorMessage, elements[0])
    cancel++
  }
  return cancel
}

// Checks if HOUR FROM is before HOUR TO
// 12:00 - 13:00 -> OK
// 13:00 - 12:00 -> ERROR
function validate_hour_input(element, second = false) {
  let container = get_hour_input_values(element, second)
  let hours = container[0]
  let elements = container[1]

  let hourFrom = hours[0].replace('00:', '24:').replace('0:', '24:')
  let hourTo = hours[1].replace('00:', '24:').replace('0:', '24:')

  let hourFromDiff =
    parseInt(hourFrom.split(':')) === 24 ? 24 : 24 - parseInt(hourTo.split(':'))
  let hourToDiff =
    parseInt(hourTo.split(':')) === 24 ? 24 : 24 - parseInt(hourTo.split(':'))

  if (hourFromDiff < hourToDiff) {
    let errorMessage = 'Closing hour cannot extend 23:59'
    render_error_message(errorMessage, elements[0])
    return 1
  }

  return 0
}

// $(".col-time input").change(function(){
//   var element = $(this).parent(".time-row");
//   validate_hour_input(element)
// })



// Regex hour input validation -> hh:mm
function validate_single_input(element) {
  let regexValidator = /^([0-1]?[0-9]|2[0-4]):([0-5][0-9])(:[0-5][0-9])?$/
  let cancel = 0

  if (!regexValidator.test(element.value)) {
    element.style.border = '2px solid red'
    cancel++
  } else {
    element.style.border = null
  }
  return cancel
}

// -------------------------------------------------- TOOLS AND ERRORS -------------------------------------------------- //

// Changes switch state to opened
function is_opened(switchId) {
  return $(switchId)[0].control.checked
}

// Checks if hours column is enabled
function is_column_active(columnElement) {
  let classNameArray = columnElement.getAttribute('class').split(' ')
  return !classNameArray.includes('disabled')
}

// Enables or disables whole hours row
function divs_enable_disable(elements, disable = false) {
  elements.forEach(function (element) {
    let divClassName = $(element).attr('class')
    if (disable) {
      if (!divClassName.includes('disabled')) divClassName += ' disabled'
    } else {
      divClassName = divClassName.replace(' disabled', '')
    }
    $(element).attr('class', divClassName)
  })
}

// Obtains hour row elements which changing their class results in visibility or invisibility of row
function get_divs_to_be_customized(inputElement) {
  let parent = inputElement.parents().eq(2).children()
  let divArray = []
  for (let i = 1; i <= 3; i++) {
    divArray.push(parent.eq(i))
  }
  return divArray
}

function input_error_handler(element, second = false) {
  let container = get_hour_input_values(element, second)
  let hourElements = container[1]
  let cancel = 0

  cancel += validate_single_input(hourElements[0])
  cancel += validate_single_input(hourElements[1])

  return cancel
}

function render_error_message(errorMessage, element) {
  let errorContainer = $(element).parents('.time-item').find(".error_here")
  let existingError = errorContainer.find('center')
  let errorElement =
    '<center id="error-message" style="color:#FF0000;">' +
    errorMessage +
    '</center>'

  existingError.remove()
  errorContainer.append(errorElement)
}
