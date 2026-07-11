from ..models import Album
from ..serializers import AlbumSerializer
from core.dependencies import photo_repository
from core.websocket.utils import send_ws_message_to_user
from core.websocket.messages import WebSocketMessageType
from django.contrib.auth.models import User
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404


class AlbumService:

    @staticmethod
    def getAll():
        albums = Album.objects.all()
        return albums

    @staticmethod
    def createAlbum(raw_data, file):
        data = raw_data.copy()
        if "image" in file and file["image"]:
            link = photo_repository.save(file["image"])
            data["cover_image"] = link

        serializer = AlbumSerializer(data=data)

        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        serializer.save()

        AlbumService._broadcast_change(
            WebSocketMessageType.ALBUM_CREATED, {"data": serializer.data}
        )
        return serializer.data

    @staticmethod
    def _replace_cover_image(data, album, file):
        if album.cover_image and album.cover_image != "":
            photo_repository.delete(album.cover_image)
        data["cover_image"] = photo_repository.save(file["image"])
        return data

    @classmethod
    def modifyAlbum(cls, id, raw_data, file):
        data = raw_data.copy()
        album = get_object_or_404(Album, pk=id)

        # The cover image is optional: a PUT without image only
        # updates the other fields (title, description...)
        if "image" in file and file["image"]:
            data = cls._replace_cover_image(data, album, file)

        serializer = AlbumSerializer(album, data=data, partial=True)

        if not serializer.is_valid():
            raise ValidationError(serializer.errors)

        serializer.save()

        cls._broadcast_change(
            WebSocketMessageType.ALBUM_UPDATED, {"data": serializer.data}
        )
        return serializer.data

    @staticmethod
    def _broadcast_change(message_type: WebSocketMessageType, message_data: dict):
        """Broadcast an album change to all authenticated users."""
        recipients = User.objects.all().values_list("id", flat=True)

        for uid in recipients:
            send_ws_message_to_user(uid, message_type, message_data)
