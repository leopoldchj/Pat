import React from "react"
import { Box } from "@mui/material"
import AlbumCard from "./AlbumCard"
import { useAlbums } from "../queries/albums"
import { useAlbumsWebSocketSync } from "../hooks/useAlbumsWebSocketSync"

function AlbumsGrid() {
    const { data: albums = [] } = useAlbums()
    useAlbumsWebSocketSync()

    return (
        <Box
            width="100%"
            display="grid"
            gridTemplateColumns="repeat(auto-fit, minmax(260px, 1fr))"
            gap={2}
            px={2}
        >
            {albums.map((album) => (
                <AlbumCard key={album.id} album={album} />
            ))}
        </Box>
    )
}

export default AlbumsGrid
