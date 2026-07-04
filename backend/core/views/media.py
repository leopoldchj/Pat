from django.http import HttpResponse
from rest_framework.views import APIView
from rest_framework.exceptions import NotFound, PermissionDenied, ValidationError

from core.models.photo import Photo
from core.models.album import Album
from core.services.media_service import MediaService
from core import media_signing

ONE_YEAR = 31536000


class BaseMediaView(APIView):
    # Public endpoint: <img> tags cannot send the JWT Authorization header.
    # Access control relies on the HMAC signature embedded in the URL,
    # which matches the opacity of the previous public S3 uuid URLs.
    authentication_classes = []
    permission_classes = []

    def _serve(self, request, file_url, signature):
        if not media_signing.verify(file_url, signature):
            raise PermissionDenied("Invalid signature")

        width = request.query_params.get("w")
        if width is not None:
            try:
                width = int(width)
            except ValueError:
                raise ValidationError({"w": "invalid width"})
            if not 0 < width <= 4096:
                raise ValidationError({"w": "invalid width"})

        data, content_type = MediaService.get_image(file_url, width)

        response = HttpResponse(data, content_type=content_type)
        response["Cache-Control"] = f"public, max-age={ONE_YEAR}, immutable"
        if request.query_params.get("download"):
            response["Content-Disposition"] = "attachment"
        return response


class MediaPhotoView(BaseMediaView):

    def get(self, request, photo_id, sig):
        try:
            photo = Photo.objects.get(pk=photo_id)
        except Photo.DoesNotExist:
            raise NotFound("Photo introuvable")
        return self._serve(request, photo.image_url, sig)


class MediaAlbumCoverView(BaseMediaView):

    def get(self, request, album_id, sig):
        try:
            album = Album.objects.get(pk=album_id)
        except Album.DoesNotExist:
            raise NotFound("Album introuvable")
        if not album.cover_image:
            raise NotFound("Album sans couverture")
        return self._serve(request, album.cover_image, sig)
