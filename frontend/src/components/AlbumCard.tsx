import React from "react"
import { Card, CardContent, CardMedia, Typography, CardActionArea, Box } from "@mui/material"
import HideImageIcon from "@mui/icons-material/HideImage"
import { Album } from "../types/album"
import mediaUrl from "../utils/mediaUrl"
import AlbumEditModal from "./UpdateAlbumModal"
import { useNavigate } from "react-router-dom"

function AlbumCard({ album }: { album: Album }) {
    const navigate = useNavigate()
    const handleClick = () => {
        navigate(`/photos/${album.id}`)
    }

    return (
        <Card
            sx={{
                height: 320,
                display: "flex",
                flexDirection: "column",
                justifyContent: "flex-start",
                borderRadius: 2,
                boxShadow: 3,
                backgroundColor: "white",
            }}
            onClick={handleClick}
        >
            <CardActionArea
                sx={{
                    flex: 1,
                    display: "flex",
                    flexDirection: "column",
                    alignItems: "stretch",
                }}
            >
                <Box sx={{ height: 180, width: "100%", position: "relative" }}>
                    {album.cover_image ? (
                        <CardMedia
                            component="img"
                            height="180"
                            image={mediaUrl(album.cover_image, { w: 480 })}
                            alt={`Couverture de l'album ${album.title}`}
                            sx={{ objectFit: "cover", height: "100%" }}
                        />
                    ) : (
                        <Box
                            sx={{
                                height: "100%",
                                backgroundColor: "#f0f0f0",
                                display: "flex",
                                alignItems: "center",
                                justifyContent: "center",
                            }}
                        >
                            <HideImageIcon sx={{ fontSize: 48, color: "#bdbdbd" }} />
                        </Box>
                    )}

                    <Box
                        sx={{
                            position: "absolute",
                            top: 8,
                            right: 8,
                            zIndex: 1,
                            backgroundColor: "rgba(255, 255, 255, 0.7)",
                            borderRadius: "50%",
                        }}
                        onClick={(e) => e.stopPropagation()}
                    >
                        <AlbumEditModal album={album} />
                    </Box>
                </Box>

                <CardContent sx={{ flex: 1, width: "100%" }}>
                    <Typography gutterBottom variant="h6" component="div" noWrap>
                        {album.title}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                        {album.description}
                    </Typography>
                    <Typography variant="body2" color="text.secondary" noWrap>
                        {album.nb_photos} photos
                    </Typography>
                    <Box mt={1}>
                        <Typography variant="caption" color="text.secondary">
                            Créé le {new Date(album.created_at).toLocaleDateString("fr-FR")}
                        </Typography>
                    </Box>
                </CardContent>
            </CardActionArea>
        </Card>
    )
}

export default AlbumCard
