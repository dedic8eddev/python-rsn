<?php

//Include Configuration
require_once (dirname (__FILE__) . '/../../../../wp-load.php');
require_once(dirname (__FILE__) . '/../classes/base.class.php');

global $dpProEventCalendar, $wpdb, $table_prefix;


class ExportEvents {
    const POST_CREATED_FIELD = 'post_date_gmt';         // NOT post_date, since we use GMT dates in Raisin CMS as well!
    const POST_MODIFIED_FIELD = 'post_modified_gmt';    // NOT post_modified, since we use GMT dates in Raisin CMS as well!

    public function __construct() {

    }

    private $dpProEventCalendar_obj;

    public function getCalendars() {
        global $wpdb;
        $cal = new DpProEventCalendar();

        $querystr = "SELECT * FROM ".$cal->table_calendar;
        $items = $wpdb->get_results($querystr, OBJECT);

        return $items;
    }

    public function get_events_for_export($id_calendar=null, $oldest_date = null) {
        global $wpdb, $dpProEventCalendar, $dpProEventCalendar_cache;

        $this->dpProEventCalendar_obj = new DpProEventCalendar( false, $calendar_id );

        $events_out = [];    

        $querystr = "SET SQL_BIG_SELECTS = 1";
        // $wpdb->query($querystr);

        $args = array( 
            'posts_per_page'    => -1, 
            'post_type'         => 'pec-events',
            'meta_key'          => 'pec_date',
            'order'             => 'ASC',
            'lang'              => (defined('ICL_LANGUAGE_CODE') ? ICL_LANGUAGE_CODE : strtolower(substr(get_locale(),3,2))),
            'orderby'           => 'meta_value',
            'suppress_filters'  => false
        );

        if($id_calendar) {
            $args['meta_query'][] = array(
                'relation' => 'OR',
                array(
                    'key'     => 'pec_id_calendar',
                    'value'   => $id_calendar,
                    'compare' => 'LIKE'
                )
            );
        }else{
                        $args['meta_query'][] = array(
                'relation' => 'OR',
                array(
                    'key'     => 'pec_id_calendar',
                    'compare' => 'NOT EXISTS',
                )
            );
        }

        if ($oldest_date) {
            // $args['meta_query'][] = array(
            //     'key'     => 'pec_date',
            //     'value'   => current_time('mysql'),
            //     'compare' => '<=',
            //     'type'    => 'DATETIME'
            // );

            $timestamp = strtotime($oldest_date);

            if($timestamp) {
                $year = date('Y', $timestamp);
                $month = date('m', $timestamp);
                $day = date('d', $timestamp);

                $args['date_query'][] = array(
                    'relation' => 'OR',

                    array(
                        'column'     => self::POST_CREATED_FIELD,
                        'inclusive' => true,
                        'after' => [
                            'year'   => $year,
                            'month'   => $month,
                            'day'   => $day,
                        ],
                    ),
                    array(
                        'column'     => self::POST_MODIFIED_FIELD,
                        'inclusive' => true,
                        'after' => [
                            'year'   => $year,
                            'month'   => $month,
                            'day'   => $day,
                        ],
                    ),
                );
            }
        }

        $query = new WP_Query($args);

        if($query->posts) {
            foreach($query->posts as $post) {
                $event = $this->get_event_full_data($post->ID);

                $events_out []= $event;
            }
        }

        return $events_out;
    }

    private function get_event_full_data($event_id) {

        $event = $this->dpProEventCalendar_obj->getEventData($event_id);

        if ( get_option('permalink_structure') ) {
            $link = rtrim(get_permalink($event->id), '/').'/'.strtotime($event->date);
        } else {
            $link = get_permalink($event->id).(strpos(get_permalink($event->id), "?") === false ? "?" : "&").'event_date='.strtotime($event->date);
        }

        if(get_post_meta($event->id, 'pec_use_link', true) && get_post_meta($event->id, 'pec_link', true) != "") {
            $link = get_post_meta($event->id, 'pec_link', true);
        }

        $author = get_userdata(get_post_field( 'post_author', $event->id ));


        // for unknown reason it does not restore the correct value here in getEventData(), so it must be done here
        $featured = get_post_meta($event->id, 'pec_featured_event', true);

        $price = get_post_meta($event->id, 'pec_phone', true);

        $post_thumbnail_id = get_post_thumbnail_id($event->id);
        $image_attributes = wp_get_attachment_image_src($post_thumbnail_id, 'small');

        if(!empty($post_thumbnail_id)) {
            $image_url = (isset($image_attributes[0])) ? $image_attributes[0] : '';
        }else{
            $image_url = '';
        }

        if(isset($event->location_id) && is_numeric($event->location_id)){
            $map_lnlat = get_post_meta($event->location_id, 'pec_venue_map_lnlat', true);
        }else{
            $map_lnlat = get_post_meta($event->id, 'pec_map_lnlat', true);
        }

        if(isset($map_lnlat) && strval($map_lnlat) != ''){
            $map_lnlat_array = explode(",", $map_lnlat);

            $lat = trim($map_lnlat_array[0]);
            $lng = trim($map_lnlat_array[1]);
        }else{
            $lat = null;
            $lng = null;
        }

        $rtl = get_post_meta($event->id, 'pec_rtl', true);

        $pro = false;

        $age_range = get_post_meta($event->id, 'pec_age_range', true);

        if(isset($age_range) && strval($age_range) != '') {
            $age_range = strtolower($age_range);
            if(preg_match('^proonly|pro[\s]+only^msi', $age_range, $outs)){
                $pro = true;
            }
        }


        $created_at = get_post_field( self::POST_CREATED_FIELD, $event->id );
        $modified_at = get_post_field( self::POST_MODIFIED_FIELD, $event->id );

        $start_ts = strtotime($event->date);
        $start_date = date('Y-m-d', $start_ts);
        $start_time = date('H:i:s', $start_ts);

        $start_datetime = date('Y-m-d H:i:s', $start_ts);

        if(isset($event->end_time_hh)&&strval($event->end_time_hh)!=''){
            $end_time_hh = $event->end_time_hh;
        }else{
            $end_time_hh = null;
        }

        if(isset($event->end_time_mm)&&strval($event->end_time_mm)!=''){
            $end_time_mm = $event->end_time_mm;
        }else{
            $end_time_mm = null;
        }

        if(strval($end_time_hh)=='' || strval($end_time_mm) == ''){
            $end_time_hh = '23';
            $end_time_mm = '59';
        }

        if ($event->end_date) {
            $end_datetime = sprintf("%s %s:%s:00", $event->end_date, $end_time_hh, $end_time_mm);
        } else {
            $end_datetime = sprintf("%s %s:%s:00", $start_date, $end_time_hh, $end_time_mm);
        }

        $row_out = [
            'id' => $event->id,
            'created_at' => $created_at,
            'modified_at' => $modified_at,

            'title' => $event->title,
            'desc' => $event->description,

            'start_datetime' => $start_datetime,
            'end_datetime' => $end_datetime,

            'author_id' => $author->ID,
            'author_name' => $author->display_name,

            'url' => $link,
            'image_url' => $image_url,

            'location_name' => $event->location,
            'location_id' => $event->location_id,
            'location_address' => $event->location_address,
            'location_address_full' => $event->map,

            'featured' => $featured,
            'pro' => $pro,

            'lat' => $lat,
            'lng' => $lng,

            'price' => $price,
            'rtl' => $rtl,

        ];

        return $row_out;
    }
}


$exporter = new ExportEvents();

// $oldest_date = (isset($_GET['oldest_date']) && $_GET['oldest_date']) ?$_GET['oldest_date'] : null;
$oldest_date = null;

if(isset($_GET['get_calendars'])) {
    $calendars = $exporter->getCalendars();
    $data_show = [];
    if($calendars) {
        foreach($calendars as $calendar) {
            $calendar_id = (int)$calendar->id;
            $row_show = [
                'id' => $calendar_id,
                'title' => $calendar->title,
                'description' => $calendar->description,
                'active' => $calendar->active,
                'events' => [],
            ];
            $events = $exporter->get_events_for_export($calendar_id, $oldest_date);
            $row_show['events'] = $events;

            $data_show []= $row_show;
        }

        $row_show = [
            'id' => 0,
            'title' => '[no calendar]',
            'description' => '[no calendar]',
            'active' => "1",
            'events' => [],
        ];

        $events = $exporter->get_events_for_export(null, $oldest_date);
        $row_show['events'] = $events;
        $data_show []= $row_show;
    }

}else{
    if(!is_numeric($_GET['calendar_id']) || $_GET['calendar_id'] <= 0) { 
        die(); 
    }

    $calendar_id = $_GET['calendar_id'];
    $oldest_date = null;
    $data_show = $exporter->get_events_for_export(1, $oldest_date);
    
}



// //date_default_timezone_set($tz); // set the PHP timezone back the way it was
header("Content-Type: application/json; charset=UTF-8");
header("Expires: Tue, 03 Jul 2001 06:00:00 GMT");
header("Last-Modified: " . gmdate("D, d M Y H:i:s") . " GMT");
header("Cache-Control: no-store, no-cache, must-revalidate");
header("Cache-Control: post-check=0, pre-check=0", false);
header("Pragma: no-cache");

echo json_encode($data_show);
