# Raisin API Documentation

These are the API's available for the Raisin Mobile:

1. Find geolocated wine posts by matching search criteria
2. Find any wine post by matching search criteria
3. Find filtered geolocated wine posts for scanned image information by specified `wine_name`, `winemaker_name`, `wine_domain`


## Find wine posts geolocated

Find closest geolocated wine posts with venue information to reference point. By default uses Paris point with 
latitude/longitude (48.864716, 2.349014). All prioritized wine posts ordered by distance. 

<u>Result list is prioritized in order:</u>
1. wine posts venue with any subscription
2. wine posts venue with no subscription   

**URL** : `api/find-wineposts/geolocated`

**Method** : `GET`

**URL Parameters**

* **search** / Optional / The search keyword to find wine posts. Lookup in wine name, wine domain, winemaker name.  
* **latitude** / Optional / The latitude of point value
* **longitude** / Optional / The longitude of point value
* **page** / Optional / The page number for the result set pagination
* **page_size** / Optional / The max amount of items per page to display

**Headers requirements**
```
Authorization: "Token realTokenValue"
Accept-Language: <language>
```

### Example Requests
```
GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?search=Rose
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?latitude=52.520008&longitude=13.404954&search=Rose
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=3&search=rose&page_size=3
```

### cURL Examples

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=3&search=rose&page_size=3' \
  --header 'Accept-Language: fr' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=1&latitude=55.0118408203125&longitude=73.36629324308842&search=Clic%20clac&page_size=5' \
  --header 'Accept-Language: en' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```

### Success Response

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=3&search=rose&page_size=3`

**Response**:
```
{
  "count": 246,
  "next": "https://devbackend2.raisin.digital/api/find-wineposts/geolocated/?page=4&page_size=3&search=rose",
  "previous": "https://devbackend2.raisin.digital/api/find-wineposts/geolocated/?page=2&page_size=3&search=rose",
  "results": [
    {
      "id": 88175,
      "color": "PINK",
      "impression_number": 0,
      "modified_time_human": "19th May 2020",
      "price_currency": "",
      "place": {
        "id": 6479,
        "name": "les enfants du marché",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/6479---CAC302B1-7485-4FAC-8D00-F1A247276DCD.png",
        "is_bar": true,
        "is_restaurant": true,
        "is_wine_shop": true,
        "likevote_number": 3,
        "i_like_it": false,
        "latitude": 48.8629451,
        "longitude": 2.362144,
        "subscription": null
      },
      "modified_time": "2020-05-19T19:07:53.780506",
      "author": {
        "id": "25d89d5b-3c54-4712-9df4-5bf14a895699",
        "has_badge": false,
        "full_name": "jessicagoraj",
        "short_name": "jessicagoraj",
        "image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/users/avatar-52013898-ABCC-495B-BA63-DFFA060F3535.png"
      },
      "wine": {
        "id": 5147,
        "winemaker_id": 1079,
        "name": "Himmel Auf Erden Rosé",
        "name_short": "Himmel Auf Erden Rosé",
        "domain": "Christian Tschida",
        "winemaker_name": "Christian Tschida"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/44ABE22C-A993-4A21-92B9-F96EB0D12FFF_tmb.png",
      "wine_year": "2018",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "WINE MADE BY A NATURAL WINEMAKER",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    },
    {
      "id": 56707,
      "color": "PINK",
      "impression_number": 0,
      "modified_time_human": "30th Jun 2019",
      "price_currency": "",
      "place": {
        "id": 1554,
        "name": "Delicatessen Cave",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/1554---20876367-ad21-11e6-835b-040164388201.jpg",
        "is_bar": false,
        "is_restaurant": false,
        "is_wine_shop": true,
        "likevote_number": 42,
        "i_like_it": false,
        "latitude": 48.8650682,
        "longitude": 2.36680560000002,
        "subscription": null
      },
      "modified_time": "2019-06-30T20:59:46.346117",
      "author": {
        "id": "762b49f8-746f-416b-a525-bc0d2c2fad77",
        "has_badge": false,
        "full_name": "gabrielbonvin",
        "short_name": "gabrielbonvin",
        "image": null
      },
      "wine": {
        "id": 29503,
        "winemaker_id": 463,
        "name": "Eau De Rose",
        "name_short": "",
        "domain": "Jean-Claude Lapalu",
        "winemaker_name": "Jean-Claude Lapalu"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/a1e495b5-87b6-4acc-b145-896726731786_tmb.jpg",
      "wine_year": "2018",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "WINE MADE BY A NATURAL WINEMAKER",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    },
    {
      "id": 60571,
      "color": "PINK",
      "impression_number": 0,
      "modified_time_human": "4th Aug 2019",
      "price_currency": "",
      "place": {
        "id": 1554,
        "name": "Delicatessen Cave",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/1554---20876367-ad21-11e6-835b-040164388201.jpg",
        "is_bar": false,
        "is_restaurant": false,
        "is_wine_shop": true,
        "likevote_number": 42,
        "i_like_it": false,
        "latitude": 48.8650682,
        "longitude": 2.36680560000002,
        "subscription": null
      },
      "modified_time": "2019-08-04T09:53:54.772669",
      "author": {
        "id": "8e3f8dc5-946b-48c3-8f6d-21d391f23f06",
        "has_badge": false,
        "full_name": "Mathieu",
        "short_name": "Mathieu",
        "image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/users/053bec5f-8fec-4267-bfd9-16bbe57cbb7a.jpg"
      },
      "wine": {
        "id": 29503,
        "winemaker_id": 463,
        "name": "Eau De Rose",
        "name_short": "",
        "domain": "Jean-Claude Lapalu",
        "winemaker_name": "Jean-Claude Lapalu"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/bb635837-42fa-4f02-805c-d698adbf470c_tmb.jpg",
      "wine_year": "2018",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "WINE MADE BY A NATURAL WINEMAKER",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    }
  ]
}
```

### Error Responses

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=3&latitude=55.0118408203125aaa&longitude=73.36629324308842&search=rose&page_size=3`

**Response**:
```
{
  "detail": "could not convert string to float: '55.0118408203125aaa'",
  "status_code": 500
}
```

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts/geolocated?page=asdf&search=rose&page_size=3`

**Response**:
```
{
  "detail": "Invalid page.",
  "status_code": 404
}
```

## Find any wine post

Find all wine posts to reference point. By default uses Paris point with latitude/longitude (48.864716, 2.349014). 
All prioritized wine posts ordered by distance. 

<u>Result list is prioritized in order:</u>
1. wine posts venue with any subscription
2. wine posts venue with no subscription 
3. wine posts not geolocated  

**URL** : `api/find-wineposts`

**Method** : `GET`

**URL Parameters**

* **search** / Optional / The search keyword to find wine posts. Lookup in wine name, wine domain, winemaker name.  
* **latitude** / Optional / The latitude of point value
* **longitude** / Optional / The longitude of point value
* **page** / Optional / The page number for the result set pagination
* **page_size** / Optional / The max amount of items per page to display

**Headers requirements**
```
Authorization: "Token realTokenValue"
Accept-Language: <language>
```

### Example Requests
```
GET https://devbackend2.raisin.digital/api/find-wineposts
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts?search=Rose
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts?latitude=52.520008&longitude=13.404954&search=Rose
```
```
https://devbackend2.raisin.digital/api/find-wineposts?page=3&search=rose&page_size=3
```

### cURL Examples

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts?page=3&search=rose&page_size=3&=' \
  --header 'Accept-Language: fr' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts?page=1&latitude=55.0118408203125&longitude=73.36629324308842&search=rose&page_size=15&=' \
  --header 'Accept-Language: fr' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```
### Success Response

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts?page=3&search=rose&page_size=2`

**Response**:
```
{
  "count": 1407,
  "next": "https://devbackend2.raisin.digital/api/find-wineposts/?page=4&page_size=2&search=rose",
  "previous": "https://devbackend2.raisin.digital/api/find-wineposts/?page=2&page_size=2&search=rose",
  "results": [
    {
      "id": 8125,
      "color": "PINK",
      "impression_number": 0,
      "modified_time_human": "28e sept 2017",
      "price_currency": "",
      "place": {
        "id": 1237,
        "name": "Saturne (permanently closed)",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/1237---saturne-table-cave.jpg",
        "is_bar": false,
        "is_restaurant": true,
        "is_wine_shop": false,
        "likevote_number": 28,
        "i_like_it": false,
        "latitude": 48.8683060993077,
        "longitude": 2.34174312579501,
        "subscription": null
      },
      "modified_time": "2017-09-28T00:05:00.494772",
      "author": {
        "id": "f25a643b-39eb-4b3f-88f1-bd4770360be1",
        "has_badge": false,
        "full_name": "mouloudour",
        "short_name": "mouloudour",
        "image": null
      },
      "wine": {
        "id": 6982,
        "winemaker_id": 557,
        "name": "Le Petit Rosé de Gimios",
        "name_short": "Le Petit Rosé de Gimios",
        "domain": "Le Petit Domaine de Gimios",
        "winemaker_name": "Anne-Marie Lavaysse"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/6B518EC1-FEA1-40F0-A6D4-007D69BD17BA_tmb.png",
      "wine_year": "2013",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "VIN FAIT PAR UN VIGNERON NATUREL",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    },
    {
      "id": 9793,
      "color": "PINK",
      "impression_number": 0,
      "modified_time_human": "21e août 2017",
      "price_currency": "",
      "place": {
        "id": 769,
        "name": "La Robe et le Palais",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/769---ebbe1ae3-aceb-11e6-835b-040164388201.png",
        "is_bar": true,
        "is_restaurant": true,
        "is_wine_shop": true,
        "likevote_number": 47,
        "i_like_it": false,
        "latitude": 48.8585736415206,
        "longitude": 2.34593541412085,
        "subscription": null
      },
      "modified_time": "2017-08-21T16:26:15.462246",
      "author": {
        "id": "7769fe3d-da2f-4616-8806-b862dc63f350",
        "has_badge": false,
        "full_name": "Avital Flores Craig",
        "short_name": "avitalflores",
        "image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/users/avatar-5DDDE368-2BD9-4EEC-AFF6-C4948E124743.png"
      },
      "wine": {
        "id": 2322,
        "winemaker_id": 306,
        "name": "Patio Rosé",
        "name_short": "Patio Rosé",
        "domain": "Viños Patio",
        "winemaker_name": "Samuel Cano"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/D4E72A69-C5C5-4CDF-808B-D6C79AA49595_tmb.png",
      "wine_year": "2016",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "VIN FAIT PAR UN VIGNERON NATUREL",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    }
  ]
}
```

### Error Responses

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts?page=abc&search=rose&page_size=2`

**Response**:
```
{
  "detail": "Page invalide.",
  "status_code": 404
}
```

## Find filtered geolocated wine posts

Find closest geolocated wine posts with venue information filtered by scanned image information:
- wine domain
- wine name
- winemaker name

All prioritized wine posts ordered by distance. 

<u>Result list is prioritized in order:</u>
1. wine posts venue with any subscription
2. wine posts venue with no subscription   

**URL** : `api/find-wineposts-filtered/geolocated`

**Method** : `GET`

**URL Parameters**

* **latitude** / Optional / The latitude of point value
* **longitude** / Optional / The longitude of point value
* **wine_domain** / Optional / The exact wine domain
* **wine_name** / Optional / The key word to search by wine name 
* **winemaker_name** / Optional / The exact winemaker name
* **page** / Optional / The page number for the result set pagination
* **page_size** / Optional / The max amount of items per page to display

**Headers requirements**
```
Authorization: "Token realTokenValue"
Accept-Language: <language>
```

### Example Requests
```
GET https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?wine_name=Per
```
```
GET https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?wine_domain=Ch%C3%A2teau%20Le%20Queyroux&wine_name=Per&winemaker_name=Dominique%20L%C3%A9andre-Chevalier
```

### cURL Examples

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?wine_name=Per' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --header 'Content-Type: application/json' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```

```
curl --request GET \
  --url 'https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?wine_domain=Ch%C3%A2teau%20Le%20Queyroux&wine_name=Per&winemaker_name=Dominique%20L%C3%A9andre-Chevalier' \
  --header 'Authorization: Token eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJ1c2VyX2lkIjoiMDU0NjIyOTYtYzY2MS00YTlkLWEzZTgtODU5NjkzNTlkNTA3IiwiZW1haWwiOiJvbGdhQG8ub28iLCJodHRwX3Jvb3QiOiJodHRwOi8vbG9jYWxob3N0IiwiZXhwIjoxOTE5NDEzMTc4LCJ1c2VybmFtZSI6InRlc3Q3In0.XgExlcPl-Hv0iqdsvHyvWq78M-_0Q2IhnAE3ODloMuk' \
  --header 'Content-Type: application/json' \
  --cookie __cfduid=da3c5914c5148cd5efbc71b05cffaa53a1611509699
```

### Success Response

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?wine_domain=Ch%C3%A2teau%20Le%20Queyroux&wine_name=Per&winemaker_name=Dominique%20L%C3%A9andre-Chevalier`

**Response**:
```
{
  "count": 1,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": 24420,
      "color": "WHITE",
      "impression_number": 0,
      "modified_time_human": "18th Mar 2018",
      "price_currency": "",
      "place": {
        "id": 2466,
        "name": "Cicchetti",
        "main_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/places/2466---20589857_252705805238502_3036929383106347008_n.jpg",
        "is_bar": true,
        "is_restaurant": false,
        "is_wine_shop": false,
        "likevote_number": 18,
        "i_like_it": false,
        "latitude": 48.8646972,
        "longitude": 2.3485317,
        "subscription": null
      },
      "modified_time": "2018-03-18T16:50:01.773586",
      "author": {
        "id": "8ce90e2a-3ac8-4c79-8ba8-8bd4729e9a56",
        "has_badge": false,
        "full_name": "nastherz12",
        "short_name": "nastherz12",
        "image": null
      },
      "wine": {
        "id": 10482,
        "winemaker_id": 2260,
        "name": "Perles de Gironde",
        "name_short": "Perles de Gironde",
        "domain": "Château Le Queyroux",
        "winemaker_name": "Dominique Léandre-Chevalier"
      },
      "thumb_image": "https://s3.eu-central-1.amazonaws.com/devassets.raisin.digital/media/posts/6652FF9B-CBF1-4ECB-9F88-EE42D3ABE91F_tmb.png",
      "wine_year": "",
      "post_status": {
        "badge": "https://devbackend2.raisin.digital/static/pro_assets/img/icon-natural.png",
        "description": "WINE MADE BY A NATURAL WINEMAKER",
        "status_short": "natural",
        "style_color": "#AD0D3A"
      }
    }
  ]
}
```

### Error Responses

**Request**: `GET https://devbackend2.raisin.digital/api/find-wineposts-filtered/geolocated?page=1a&wine_domain=Ch%C3%A2teau%20Le%20Queyroux&wine_name=Per&winemaker_name=Dominique%20L%C3%A9andre-Chevalier`

**Response**:
```
{
  "detail": "Invalid page.",
  "status_code": 404
}
```
