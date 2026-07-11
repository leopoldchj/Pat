from django.urls import path
from .views import (
    MessageView,
    PaginatedMessageView,
    ProfileView,
    BucketPointView,
    PresenceIndicatorView,
    AlbumView,
    PhotoView,
    PhotoDetailView,
    PhotoMoveView,
    PhotoCopyView,
    MediaPhotoView,
    MediaAlbumCoverView,
)

urlpatterns = [
    path("messages/", MessageView.as_view(), name="user_messages"),
    path(
        "messages/paginated/",
        PaginatedMessageView.as_view(),
        name="user_messages_paginated",
    ),
    path("messages/<int:pk>/", MessageView.as_view(), name="user_messages"),
    path("profile/", ProfileView.as_view(), name="user_profile"),
    path("bucketpoints/", BucketPointView.as_view(), name="bucket_points"),
    path("bucketpoints/<int:pk>/", BucketPointView.as_view(), name="bucket_points"),
    path("presence/", PresenceIndicatorView.as_view(), name="presence_indicator"),
    path("albums/", AlbumView.as_view(), name="albums"),
    path("albums/<int:album_id>/", AlbumView.as_view(), name="album_edition"),
    path("photos/<int:album_id>/", PhotoView.as_view(), name="photo_view"),
    path(
        "photos/<int:album_id>/<int:photo_id>/",
        PhotoDetailView.as_view(),
        name="photo_detail",
    ),
    path(
        "photos/<int:album_id>/<int:photo_id>/move/",
        PhotoMoveView.as_view(),
        name="photo_move",
    ),
    path(
        "photos/<int:album_id>/<int:photo_id>/copy/",
        PhotoCopyView.as_view(),
        name="photo_copy",
    ),
    path(
        "media/photos/<int:photo_id>/<str:sig>/",
        MediaPhotoView.as_view(),
        name="media_photo",
    ),
    path(
        "media/albums/<int:album_id>/cover/<str:sig>/",
        MediaAlbumCoverView.as_view(),
        name="media_album_cover",
    ),
]
