# Image format and naming

### Technical information

The MediaStorage class contains storage-related functions for image and file processing. 
Take note that the `get_available_name` function behaves differently for Vuforia images 
(forces overwrite of image named using the standard)

`/web/utils/storage.py`

Module contains most image manipulation functions: `web/utils/images.py`

Module contains the image models: `web/models/images.py`


### Useful shorthand

`aws_url` function in `web/utils/upload_tools.py` generates the link for an image file. 

Parameter `thumb=True` appends the `_tmb` suffix where needed. 
Parameter `square=True` appends the `_square` suffix where needed.

Take care that `aws_url_events` is a bit different, since legacy events use an external image url instead of the one with our standards.

`ImageUrlField` and `ImageUrlThumbField` from `web/serializers/utils.py` are useful shorthand for serializer fields that use the image links.


### Temp images

For places and winemakers, there are drop zones, that upload the files, even when the object is not created. 

This means that, when a place or winemaker is created, the related images and files first get attached to a provisional "parent", 
then moved to the proper S3 path and assigned onto the object. 

See the `update_filename` function in `web/utils/filenames.py` and the contents of `web/utils/temp_images.py` file, 
which includes path definitions, functionalities for moving to the final parent, retrieval, deletion etc.

### Vuforia images
There are 3 ways of creating a Vuforia Image:
- by promoting an image from a winepost (`create_from_x_image`)
- by uploading it directly (`create_vuforia_image_from_file`)
- from the Pixie photo editor using b64 data directly (`create_from_b64_data`)

### Displaying HEIC previews and HEIF/HEIC conversion

 - there is a JS trick that calls an API endpoint to display HEIC previews before they are converted to JPG. 
 This is needed for Dropzone and Dropify to show a thumbnail preview, before the upload is finalised. 
 The endpoint name is `convert-heic/` and uses `pyheif` to retrieve a proper jpeg preview.
 - it is not a problem after uploading, since all image files are converted to JPGs.
 - the library `pyheif` has some known issues, as documented in Icebox tickets. 
 Not all heif files are properly converted, but there is nothing we can use in its stead.

#### Conversion
The image is converted to RBG mode and saved as .jpg. 
For transparent PNGs, we use a method that ensures transparency looks good. 
For HEIF/HEIC files we use a conversion library.

#### Renaming

 - Files are renamed with a built-in safe renaming function from `boto3/AWS S3` library, which removes, among others: diacritics, special characters, apostrophes, quotes, spaces etc.
 - Uniqueness is ensured from the boto3 library. In case a duplicate file is found, there will be a unique suffix appended to the image file name. There is an exception to this: vuforia images are named through a standard containing the wine id and winepost id, meaning that the file is rewritten if reuploaded.
 
#### Resizing & thumbnails

 - the main image is homeothetically resized to width max: 760px
 - the thumbnail `_tmb` is a square of 400px400px. Thumbnails of portrait-oriented images are centered crops of the original picture. 
 - the square `_square` images are with size of 260x260 px.
 
**Thumbnail naming convention:**
- assume `main_image_name.jpg`
- thumbnail will be called `main_image_name_tmb.jpg` -> exists for previous images as well.
- square thumbnail will be called `main_image_name_square.jpg`

----------------

### We have 3 different types of images: 
1 - Full image

2 - Thumbnails

3 - Square images

----------------
**1 - Full image =  image_name.jpg = max-width:760px**

Portrait-oriented images or landscape-oriented images should always be respecting the original ratio (same proportions) with a max-width:760px.   
If original image is smaller than 760px then we do not resize it. 
- USED: on apps and whenever its is best to show large images. 
Used once Vuforia scanning is done. 

SCANNING: When using the scanning feature, you can publish using Vuforia screens or when the auto-completion screen. Image processing is therefore very different. However both require image optimisation. 

**2 - Thumbnails = image_name_tmb.jpg = max-width:400x400px** 

- USED: on apps, map's thumbnails. 

**3 - Square images = - image_name_square.jpg = max-width:260x260px** 

- USED: on the Pro. Dashboard website: example: https://cms.raisin.digital/pro/dashboard/11862  

### RESIZING EXAMPLES: 
A - Original image size: **500x600**
- Full image = **500x600**
- Thumbnails = 400x400
- Square images = 260x260

B - Original image size: **300x600**
- Full image = **300x600**
- Thumbnails = 400x400
- Square images = 260x260

C - Original image size: **300x200**
- Full image = **300x200**
- Thumbnails = 400x400
- Square images = 260x260
 
D - Original image size: **1500x1000** ( Landscape MODE)
- Full image = 760x506 (rounded from 506.67)
- Thumbnails = 400x400
- Square images = 260x260