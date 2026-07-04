import getBaseURL from "./utils"

// The API returns media paths like /api/media/photos/<id>/<sig>/?v=...
// In dev the backend lives on another origin (REACT_APP_API_URL); in prod
// nginx serves both under the same origin.
function apiOrigin(): string {
    return process.env.NODE_ENV === "development"
        ? new URL(process.env.REACT_APP_API_URL as string).origin
        : getBaseURL()
}

export default function mediaUrl(path: string, opts?: { w?: number; download?: boolean }): string {
    const url = new URL(path, apiOrigin())
    if (opts?.w) url.searchParams.set("w", String(opts.w))
    if (opts?.download) url.searchParams.set("download", "1")
    return url.toString()
}
