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

    googleApiKey: 'AIzaSyCaXyEdOIMYrpt8PuKImOSBjBHegwzkx-w',

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

    cacheBust: ''
});

// Codes to be execute when all JS files are loaded and ready to use
//
app.ready(function () {
    // Page: invoices.html
    // Add a new item row in "create new invoice"
    //
    $(document).on('click', '#btn-new-item', function () {
        var html =
            '' +
            '<div class="form-group input-group flex-items-middle">' +
            '<select title="Item" data-provide="selectpicker" data-width="100%">' +
            '<option>Website design</option>' +
            '<option>PSD to HTML</option>' +
            '<option>Website re-design</option>' +
            '<option>UI Kit</option>' +
            '<option>Full Package</option>' +
            '</select>' +
            '<div class="input-group-input">' +
            '<input type="text" class="form-control">' +
            '<label>Quantity</label>' +
            '</div>' +
            '<a class="text-danger pl-12" id="btn-remove-item" href="#" title="Remove" data-provide="tooltip"><i class="ti-close"></i></a>' +
            '</div>';

        $(this).before(html);
    });

    // Page: invoices.html
    // Remove an item row in "create new invoice"
    //
    $(document).on('click', '#btn-remove-item', function () {
        $(this)
            .closest('.form-group')
            .fadeOut(function () {
                $(this).remove();
            });
    });

    if ($('.dropify').length > 0) {
        $('.dropify').dropify({
            tpl: {
                wrap: '<div class="dropify-wrapper"></div>',
                loader: '<div class="dropify-loader"></div>',
                message: '<div class="dropify-message"><i class="fa fa-upload lead"></i></div>',
                preview:
                    '<div class="dropify-preview"><span class="dropify-render"></span><div class="dropify-infos"><div class="dropify-infos-inner"><p class="dropify-infos-message">{{ replace }}</p></div></div></div>',
                filename: '<p class="dropify-filename"><span class="file-icon"></span> <span class="dropify-filename-inner"></span></p>',
                clearButton:
                    '<button type="button" class="dropify-clear btn btn-square btn-danger btn-delete"><i class="fa fa-trash-o"></i></button>',
                errorLine: '<p class="dropify-error">{{ error }}</p>',
                errorsContainer: '<div class="dropify-errors-container"><ul></ul></div>'
            }
        });
    }

    $(document).on('click', '.img-item .btn-delete', function () {
        $(this).parents('.sortable-row').find('.dropify-wrapper').removeClass('disabled');
        $(this).parents('.sortable-row').find('[data-provide="dropify"]').removeAttr('disabled');
        $(this)
            .parents('.img-item')
            .remove();
        return false;
    });

    var inputs = document.querySelectorAll(".intlTel");
    if (inputs.length > 0) {
        inputs.forEach(input => {
            window.intlTelInput(input, {
                dropdownContainer: document.body,
                utilsScript: "pro_assets/js/utils.js",
            });
        });

    }

    $(document).on('change', '.toogle-opening', function () {
        $(this).parents('.time-item').find('.col-time, .col-action').toggleClass('disabled');
        $(this).parents('.time-item').find('.btn-show-hours').removeClass('disabled');
        if (!$(this).isChecked) {
            $(this).parents('.time-item').find('.opening2').addClass('disabled');
            $(this).parents('.time-item').find('.time .form-control').val('');
        }
        return false;
    });

    $(document).on('change', '.toogle-closing', function () {
        if (!$(this).prop('checked')) {
            var target = $(this).data('target');
            $(target).datepicker('update', '');
        }
        return false;
    });

    showSecondTimeRow();
    initDeleteLine();
    addNewDate();
    initDeleteHoliday();
    initDate();

    // Wines name
    if ($('.js-typeahead-wines-name').length > 0) {
        typeof $.typeahead({
            input: '.js-typeahead-wines-name',
            highlight: false,
            dynamic: true, 
            delay: 250,
            minLength: 3,
            accent: true,
            maxItem:0,
            source: {
                ajax: function (query) {
                    return {
                        type: "GET",
                        headers: {
                            "accept-language": userLang
                        },  
                        url: "/pro/ajax/typeahead/wine_name/",
                        dataType: 'json',
                        path: "result",
                        data: {
                            q: "{{query}}"
                        }
                    }
                }
            },
            display: ['name', 'winemaker__name', 'domain','image','color','grape_variety'],
            templateValue: '{{name}}',
            template: '<div class="wine_data"><span class="wine-name">{{name}} <img src={{image}}></span><span class="domain">{{winemaker__name}}</span> <span class="name">{{domain}}</span></div>',
            callback: {
                onClick: function (node, a, item, event) {
                        console.log(item)
                    $('#n-ame-typeahead').val(item.name);
                    $('#winemakers-typeahead').val(item.winemaker__name);
                    $('#domain-typeahead').val(item.domain);  
                    $('#wine-grape-variety-id').val(item.grape_variety);        
                    $('#n-ame-typeahead-add').val(item.name).parents('.form-group').addClass('do-float');
                    $('#winemakers-typeahead-add').val(item.winemaker__name).parents('.form-group').addClass('do-float');
                    $('#domain-typeahead-add').val(item.domain).parents('.form-group').addClass('do-float');
                    $('#wine-grape-variety-add').val(item.grape_variety).parents('.form-group').addClass('do-float');  
                    $("#sparkling-add").prop("checked", item.is_sparkling);
                    select_wine_color(item.color)
                    select_add_wine_color(item.color,true)
                }
            }
        })


    }

    // Domains name
    if ($('.js-typeahead-domain-name').length > 0) {
        typeof $.typeahead({
            input: '.js-typeahead-domain-name',
            order: 'desc',
            source: {
                data: [
                    'Alexandre Bain', 'Amunategui', 'Binner', 'Escarpolette', 'Foulards rouges', 'La Cave d’Ivry',
                    'Le Rubis', 'Partida Creus', 'Yoyo']
            }
        });
    }

    // Winemaker
    if ($('.js-typeahead-winemaker').length > 0) {
        typeof $.typeahead({
            input: '.js-typeahead-winemaker',
            order: 'desc',
            source: {
                data: [
                    'Julien Veyret-Ketel', 'Julien Courtois & Heidi Kuka', 'Julien Ditté & Olivier Cazenave',
                    'Julien Guillon', 'Julien Flauw', 'Julien Auroux', 'Julien Mareschal']
            }
        });
    }
    


    if ($('.sortable-row').length > 0) {
        var width = $('.sortable-row').width() / 6;
        $('.sortable.list .img-item').css('width', width + 'px');
    }

    $(document).on('mouseover', '.graph-area', function () {
        $(this).prev('.morris-hover').hide();
    });
    $(document).on('mouseleave', '.graph-area', function () {
        $(this).prev('.morris-hover').show();
    });

    if ($('#popup-autoshow').length > 0) {
        var delay = $('#popup-autoshow').data('autoshow');
        setTimeout(function () {
            $('#popup-autoshow').addClass('show');
            var timer = $('#popup-autoshow').data('autohide');
            setTimeout(function () {
                $('#popup-autoshow').removeClass('show');
            }, timer);
        }, delay);

        $('[data-dismiss="popup"]').click(function () {
            $(this).parent('.popup').removeClass('show');
        });
    }

});

function initDate() {
        if ($('[data-provide="datepicker"]').length > 0) {


            $('[data-provide="datepicker"]').datepicker({
                format: "dd/mm/yyyy"
            }).on('changeDate', function (e) {
                var target = $(this).data('target');
                $(target).prop('checked', true);
            });


            $('[data-provide="datepicker"]').datepicker().on('clearDate', function (e) {
                var target = $(this).data('target');
                $(target).prop('checked', false);
            });

            $('#holidays-list-range').on('focus', '.input-daterange', function(){
                $(this).datepicker({
                    format: "dd/mm/yyyy"
                }).on('changeDate', function (e) {
                    var target = $(this).data('target');
                    $(target).prop('checked', true);
                });    
            });

            
            $('#holidays-list-range').on('focus', '.input-daterange', function(){
                $(this).datepicker().on('clearDate', function (e) {
                    var target = $(this).data('target');
                    $(target).prop('checked', false);
                });
            });
       }
}

function addNewDate() {
    $(document).on('click', '.btn-add-new-date', function () {
        var index = $('#holidays-list .time-item').length + 1;
        var html = $('#holidays-list .time-item').eq(0).html();
        var searchStr = 'holiday';
        var replaceStr = 'holiday' + index;

        let divIndex = html.lastIndexOf("</div>");
      //  html = html.substring(0, divIndex) + "<button class=\"btn btn-link btn-delete-holiday\"><i class=\"ti-close\"></i></button></div>";

        html = '<div class="form-group time-item">' + replaceAll(searchStr, replaceStr, html) + '</div>';
        $('#holidays-list').append(html);
        initDate();
        return false;
    });

    $(document).on('click', '.btn-add-new-date-range', function () {
        var index = $('#holidays-list-range .time-item').length + 1;
        var html = $('#holidays-list-range .time-item').eq(0).html();
        var searchStr = 'date-range';
        var replaceStr = 'date-range' + index;

        let divIndex = html.lastIndexOf("</div>");
      //  html = html.substring(0, divIndex) + "<button class=\"btn btn-link btn-delete-holiday\"><i class=\"ti-close\"></i></button></div>";

        html = '<div class="form-group time-item">' + replaceAll(searchStr, replaceStr, html) + '</div>';
        $('#holidays-list-range').append(html);
        //initDate();
        return false;
    });
}

function showSecondTimeRow() {
    $(document).on('click', '.btn-show-hours', function () {
        $(this).parents('.time-item').find('.opening2').removeClass('disabled');
        $(this).addClass('disabled');
        return false;
    });
}

function initDeleteLine() {
    $(document).on('click', '.btn-delete-line', function () {
        var current = $(this).parents('.time-item');
        var nbItems = $(current).find('.time-row').length;
        if ($(this).parents('.time-row').hasClass('opening2')) {
            $(this).parents('.opening2').addClass('disabled');
            if (nbItems == 2 && $(current).find('.opening2').hasClass('disabled')) {
                $(current).find('.btn-show-hours').removeClass('disabled');
            }
        } else {
            if (nbItems == 3 && $(current).find('.opening2').hasClass('disabled')) {
                $(current).find('.btn-show-hours').removeClass('disabled');
            }
            $(this).parents('.time-row').remove();
            $(current).find('.time-row:last-child').find('.btn-add-hours').removeClass('disabled');
        }
        return false;
    });
}

function initDeleteHoliday() {
    $(document).on('click', 'button[class*="btn-delete-holiday"]', function () {
        $(this).parents('.time-item').remove();
        return false;
    });
}

function replaceAll(searchStr, replaceStr, toBeReplacedStr) {
    return toBeReplacedStr.split(searchStr).join(replaceStr);
}

function getQueryVariable(variable) {
    var query = window.location.search.substring(1);
    var vars = query.split("&");
    for (var i = 0; i < vars.length; i++) {
        var pair = vars[i].split("=");
        if (pair[0] == variable) {
            return pair[1];
        }
    }
    return (false);
}



