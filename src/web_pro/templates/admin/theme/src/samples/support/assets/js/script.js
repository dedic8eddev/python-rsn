'use strict';


app.config({

  /*
  |--------------------------------------------------------------------------
  | Autoload
  |--------------------------------------------------------------------------
  |
  | By default, the app will load all the required plugins from /pro_assets/vendor/
  | directory. If you need to disable this functionality, simply change the
  | following variable to false. In that case, you need to take care of loading
  | the required CSS and JS files into your page.
  |
  */

  autoload: true,

  /*
  |--------------------------------------------------------------------------
  | Provide
  |--------------------------------------------------------------------------
  |
  | Specify an array of the name of vendors that should be load in all pages.
  | Visit following URL to see a list of available vendors.
  |
  | https://thetheme.io/theadmin/help/article-dependency-injection.html#provider-list
  |
  */

  provide: [],

  /*
  |--------------------------------------------------------------------------
  | Google API Key
  |--------------------------------------------------------------------------
  |
  | Here you may specify your Google API key if you need to use Google Maps
  | in your application
  |
  | Warning: You should replace the following value with your own Api Key.
  | Since this is our own API Key, we can't guarantee that this value always
  | works for you.
  |
  | https://developers.google.com/maps/documentation/javascript/get-api-key
  |
  */

  googleApiKey: '',

  /*
  |--------------------------------------------------------------------------
  | Google Analytics Tracking
  |--------------------------------------------------------------------------
  |
  | If you want to use Google Analytics, you can specify your Tracking ID in
  | this option. Your key would be a value like: UA-XXXXXXXX-Y
  |
  */

  googleAnalyticsId: '',

  /*
  |--------------------------------------------------------------------------
  | Smooth Scroll
  |--------------------------------------------------------------------------
  |
  | By changing the value of this option to true, the browser's scrollbar
  | moves smoothly on scroll.
  |
  */

  smoothScroll: true,

  /*
  |--------------------------------------------------------------------------
  | Save States
  |--------------------------------------------------------------------------
  |
  | If you turn on this option, we save the state of your application to load
  | them on the next visit (e.g. make topbar fixed).
  |
  | Supported states: Topbar fix, Sidebar fold
  |
  */

  saveState: false,

  /*
  |--------------------------------------------------------------------------
  | Cache Bust String
  |--------------------------------------------------------------------------
  |
  | Adds a cache-busting string to the end of a script URL. We automatically
  | add a question mark (?) before the string. Possible values are: '1.2.3',
  | 'v1.2.3', or '123456789'
  |
  */

  cacheBust: '',


});




// Codes to be execute when all JS files are loaded and ready to use
//
app.ready(function() {



  // Popular categories chart
  //
  if ( window["Chart"] !== undefined ) {
    var chartjs_cat = new Chart($("#chartjs-cat"), {
      type: 'line',
      data: {
        labels: ["January", "February", "March", "April", "May", "June"],
        datasets: [
          {
            label: "Plugins",
            fill: false,
            borderWidth: 3,
            borderColor: "#9966ff",
            pointBackgroundColor: "#9966ff",
            pointBorderColor: "#9966ff",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "#9966ff",
            data: [9, 12, 11, 14, 22, 18]
          },
          {
            label: "Gruntjs",
            fill: false,
            borderWidth: 3,
            borderColor: "#4bc0c0",
            pointBackgroundColor: "#4bc0c0",
            pointBorderColor: "#4bc0c0",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "#4bc0c0",
            data: [6, 10, 10, 17, 20, 16]
          },
          {
            label: "Bootstrap",
            fill: false,
            borderWidth: 3,
            borderColor: "#ff9f40",
            pointBackgroundColor: "#ff9f40",
            pointBorderColor: "#ff9f40",
            pointHoverBackgroundColor: "#fff",
            pointHoverBorderColor: "#ff9f40",
            data: [5, 9, 12, 13, 17, 20]
          }
        ]
      },
      options: {
        legend: {
          display: false
        },
      }
    });
  }



  //----------------------------------------------------/
  // Enable delete button when a row selected
  //----------------------------------------------------/
  $(document).on('change', '[data-provide*="selectall"] .custom-checkbox input', function(){
    toolbarDisableButtons();
  });

  var toolbarDisableButtons = function() {
    if ( $('.media .custom-checkbox input:checked').length ) {
      $('.media-list-header .btn.disableable.disabled').removeClass('disabled');
    }
    else {
      $('.media-list-header .btn.disableable').addClass('disabled');
    }
  }
  toolbarDisableButtons();




  //----------------------------------------------------/
  // Category name and slug
  //----------------------------------------------------/
  $('#cat-name').on('change', function(){
    if ( $('#cat-slug').val() != '' ) {
      return;
    }

    $('#cat-slug').val( $(this).val().replace(/\s+/g, '-').toLowerCase() );
  });



  //----------------------------------------------------/
  // Global action buttons
  //----------------------------------------------------/

  // Delete
  //
  $(document).on('click', '[data-perform="delete"]', function() {
    var url = $(this).data('target');
    var ids = '';
    var item = $(this);

    app.modaler({
      html: 'Are you sure you want to delete selected items? Delete is permanently!',
      type: 'top',
      size: 'sm',
      title: 'Delete confirmation',
      confirmText: 'Yes',
      cancelVisible: true,
      cancelText: 'No',

      onConfirm: function(modal) {

        if ( item.closest('tr').length ) {
          ids = item.closest('tr').fadeOut(900).data('id');
        }
        else {
          $('.media-list .media .custom-checkbox input:checked').each(function(){
            ids += $(this).closest('.media').fadeOut(900).data('id') + ',';
          });
        }

        $.post(url, {id: ids}, function(data){
          // On success
          app.toast('Selected items deleted successfully.')
        });
      }
    });
  });




  // Delete single
  //
  $(document).on('click', '[data-perform="delete-single"]', function() {
    var url = $(this).data('target');
    var ids = '';
    var item = $(this);

    app.modaler({
      html: 'Are you sure you want to delete this items? Delete is permanently!',
      type: 'top',
      size: 'sm',
      title: 'Delete confirmation',
      confirmText: 'Yes',
      cancelVisible: true,
      cancelText: 'No',

      onConfirm: function(modal) {

        if ( item.closest('tr').length ) {
          ids = item.closest('tr').fadeOut(900).data('id');
        }
        else {
          ids = item.closest('.media').fadeOut(900).data('id');
        }

        $.post(url, {id: ids}, function(data){
          // On success
          app.toast('Selected items deleted successfully.')
        });
      }
    });
  });



  // Edit
  //
  $(document).on('click', '[data-perform="edit"]', function() {
    app.modaler({
      url: $(this).data('target'),
      type: 'top',
      size: 'sm',
      title: 'Edit',
      confirmText: 'Save',
      cancelVisible: true,

      onConfirm: function(modal) {
        modal.find('form').submit();
      }
    });
  });




  // Toggle star
  //
  $(document).on('change', '[data-perform="toggle-star"]', function(){
    var url = $(this).data('target');
    var id = $(this).closest('.media').data('id');
    app.toast(id);

    $.post(url, {id: id}, function(data){

    });
  });



});
