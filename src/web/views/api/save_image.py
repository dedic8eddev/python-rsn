from web.utils.storage import MediaStorage
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from raisin import settings
from web.utils.upload_tools import aws_url
from django.views.decorators.csrf import csrf_exempt


# /api/images/save-image/
# usual image upload function, which can be used both as API and usual function
# created for Text Editor uploading image functionality
@api_view(['POST'])
@permission_classes([AllowAny, ])
@csrf_exempt
def save_image(request):
    image = request.data['image']
    storage = MediaStorage(bucket=settings.AWS_STORAGE_BUCKET_NAME)
    original_name = str(image)
    storage._save(content=image, name=original_name)
    image_name = storage.generate_thumbnails(
        name=original_name,
        content=image,
        convert_to_jpg=False,
        save_full_image=True,
        save_thumb_image=False,
        save_square_image=False
    )

    return Response(aws_url(image_name))
