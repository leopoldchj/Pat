import hashlib

from rest_framework import serializers
from ..models.album import Album
from ..models.photo import Photo
from .. import media_signing


def media_cache_buster(file_url: str) -> str:
    return hashlib.sha1(file_url.encode()).hexdigest()[:8]


class AlbumSerializer(serializers.ModelSerializer):
    nb_photos = serializers.SerializerMethodField()

    class Meta:
        model = Album
        fields = [
            "id",
            "title",
            "description",
            "created_at",
            "updated_at",
            "cover_image",
            "nb_photos",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # The S3 URL stays in DB; the API exposes the backend media proxy instead
        if data.get("cover_image"):
            sig = media_signing.sign(instance.cover_image)
            v = media_cache_buster(instance.cover_image)
            data["cover_image"] = f"/api/media/albums/{instance.id}/cover/{sig}/?v={v}"
        return data

    def get_nb_photos(self, album):
        return Photo.objects.filter(album=album).count()

    def create(self, validated_data):
        request = self.context.get("request")
        if request and not request.user.is_authenticated:
            return None
        return super().create(validated_data)
