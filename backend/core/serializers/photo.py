from rest_framework import serializers
from ..models.photo import Photo
from .. import media_signing
from .album import AlbumSerializer, media_cache_buster


class PhotoSerializer(serializers.ModelSerializer):
    album = AlbumSerializer(read_only=True)

    class Meta:
        model = Photo
        fields = [
            "id",
            "album",
            "image_url",
            "caption",
            "created_at",
            "updated_at",
            "location",
        ]
        read_only_fields = ["created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Block image_url modification on update (PATCH) — pure DB edit only
        if self.instance is not None:
            self.fields["image_url"].read_only = True

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # The S3 URL stays in DB; the API exposes the backend media proxy instead
        if data.get("image_url"):
            sig = media_signing.sign(instance.image_url)
            v = media_cache_buster(instance.image_url)
            data["image_url"] = f"/api/media/photos/{instance.id}/{sig}/?v={v}"
        return data

    def create(self, validated_data):
        request = self.context.get("request")
        if request and not request.user.is_authenticated:
            return None
        # serializer.save(album=...) injects album into validated_data:
        # pop it so it is never passed twice to objects.create()
        album = validated_data.pop("album", None) or self.context.get("album")
        if not album:
            raise serializers.ValidationError({"album": "Album manquant"})

        return Photo.objects.create(album=album, **validated_data)


class TargetAlbumSerializer(serializers.Serializer):
    target_album_id = serializers.IntegerField()
