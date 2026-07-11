import { useEffect, useState, useCallback } from "react"
import { useGetPhotos } from "../queries/photos"
import { useWebSocketContext } from "../contexts/WebSocketProvider"
import { WebSocketMessageType } from "../types/websockets"
import {
    PhotoUploaded,
    PhotoDeleted,
    PhotoUpdated,
    PhotoMoved,
    PhotoCopied,
} from "../types/websocket-interfaces"
import { Photo } from "../types/photo"

interface UsePhotosWithWebSocketResult {
    photos: Photo[]
    isLoading: boolean
    isError: boolean
    refetch: () => void
}

/**
 * Hook that combines react-query photo fetching with WebSocket real-time updates.
 * Automatically updates the photo list when photos are added, deleted, or updated.
 */
export function usePhotosWithWebSocket(albumId: string): UsePhotosWithWebSocketResult {
    const { data, isLoading, isError, refetch } = useGetPhotos(albumId)
    const [photos, setPhotos] = useState<Photo[]>([])
    const websocket = useWebSocketContext()

    // Sync with react-query data
    useEffect(() => {
        if (data?.photos) {
            setPhotos(data.photos)
        }
    }, [data?.photos])

    // Handle photo uploaded event
    const handlePhotoUploaded = useCallback(
        (payload: PhotoUploaded) => {
            // Only update if the photo is for the current album
            if (String(payload.album_id) !== String(albumId)) {
                return
            }

            console.debug("Photo uploaded via WebSocket:", payload.data.id)
            setPhotos((prev) => {
                // Check if photo already exists (avoid duplicates from own uploads)
                if (prev.some((p) => p.id === payload.data.id)) {
                    return prev
                }
                // Add new photo at the beginning (most recent first)
                return [payload.data, ...prev]
            })
        },
        [albumId]
    )

    // Handle photo deleted event
    const handlePhotoDeleted = useCallback(
        (payload: PhotoDeleted) => {
            // Only update if the photo is for the current album
            if (String(payload.album_id) !== String(albumId)) {
                return
            }

            console.debug("Photo deleted via WebSocket:", payload.id)
            setPhotos((prev) => prev.filter((photo) => photo.id !== payload.id))
        },
        [albumId]
    )

    // Handle photo updated event
    const handlePhotoUpdated = useCallback(
        (payload: PhotoUpdated) => {
            // Only update if the photo is for the current album
            if (String(payload.album_id) !== String(albumId)) {
                return
            }

            console.debug("Photo updated via WebSocket:", payload.data.id)
            setPhotos((prev) =>
                prev.map((photo) =>
                    photo.id === payload.data.id ? { ...photo, ...payload.data } : photo
                )
            )
        },
        [albumId]
    )

    // Handle photo moved event: remove from source album, add to target album
    const handlePhotoMoved = useCallback(
        (payload: PhotoMoved) => {
            if (String(payload.source_album_id) === String(albumId)) {
                console.debug("Photo moved out via WebSocket:", payload.data.id)
                setPhotos((prev) => prev.filter((photo) => photo.id !== payload.data.id))
            } else if (String(payload.target_album_id) === String(albumId)) {
                console.debug("Photo moved in via WebSocket:", payload.data.id)
                setPhotos((prev) => {
                    if (prev.some((p) => p.id === payload.data.id)) {
                        return prev
                    }
                    return [payload.data, ...prev]
                })
            }
        },
        [albumId]
    )

    // Handle photo copied event: add the new photo to the target album
    const handlePhotoCopied = useCallback(
        (payload: PhotoCopied) => {
            if (String(payload.album_id) !== String(albumId)) {
                return
            }

            console.debug("Photo copied via WebSocket:", payload.data.id)
            setPhotos((prev) => {
                if (prev.some((p) => p.id === payload.data.id)) {
                    return prev
                }
                return [payload.data, ...prev]
            })
        },
        [albumId]
    )

    // Subscribe to WebSocket events
    useEffect(() => {
        websocket.bind(WebSocketMessageType.PhotoUploaded, handlePhotoUploaded)
        websocket.bind(WebSocketMessageType.PhotoDeleted, handlePhotoDeleted)
        websocket.bind(WebSocketMessageType.PhotoUpdated, handlePhotoUpdated)
        websocket.bind(WebSocketMessageType.PhotoMoved, handlePhotoMoved)
        websocket.bind(WebSocketMessageType.PhotoCopied, handlePhotoCopied)

        return () => {
            websocket.unbind(WebSocketMessageType.PhotoUploaded, handlePhotoUploaded)
            websocket.unbind(WebSocketMessageType.PhotoDeleted, handlePhotoDeleted)
            websocket.unbind(WebSocketMessageType.PhotoUpdated, handlePhotoUpdated)
            websocket.unbind(WebSocketMessageType.PhotoMoved, handlePhotoMoved)
            websocket.unbind(WebSocketMessageType.PhotoCopied, handlePhotoCopied)
        }
    }, [
        websocket,
        handlePhotoUploaded,
        handlePhotoDeleted,
        handlePhotoUpdated,
        handlePhotoMoved,
        handlePhotoCopied,
    ])

    return {
        photos,
        isLoading,
        isError,
        refetch,
    }
}
