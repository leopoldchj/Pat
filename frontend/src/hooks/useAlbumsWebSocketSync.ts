import { useEffect } from "react"
import { useQueryClient } from "@tanstack/react-query"
import { useWebSocketContext } from "../contexts/WebSocketProvider"
import { WebSocketMessageType } from "../types/websockets"

// Album and photo events that can change the albums list
// (photo events affect nb_photos and cover freshness)
const ALBUM_RELATED_EVENTS = [
    WebSocketMessageType.AlbumCreated,
    WebSocketMessageType.AlbumUpdated,
    WebSocketMessageType.PhotoUploaded,
    WebSocketMessageType.PhotoDeleted,
    WebSocketMessageType.PhotoMoved,
    WebSocketMessageType.PhotoCopied,
]

/**
 * Keeps the react-query "albums" cache in sync with WebSocket events.
 * Any album or photo change triggers a refetch of the albums list.
 */
export function useAlbumsWebSocketSync(): void {
    const websocket = useWebSocketContext()
    const queryClient = useQueryClient()

    useEffect(() => {
        const invalidateAlbums = () => {
            queryClient.invalidateQueries({ queryKey: ["albums"] })
        }

        ALBUM_RELATED_EVENTS.forEach((event) => websocket.bind(event, invalidateAlbums))

        return () => {
            ALBUM_RELATED_EVENTS.forEach((event) => websocket.unbind(event, invalidateAlbums))
        }
    }, [websocket, queryClient])
}
