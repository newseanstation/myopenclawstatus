---
name: youtube-ytdlp
description: Use yt-dlp (no Maton required) to search YouTube and fetch metadata (titles, ids, URLs) for videos/channels/playlists.
metadata: {"openclaw":{"requires":{"bins":["yt-dlp"]},"homepage":"https://github.com/yt-dlp/yt-dlp"}}
---

# YouTube via yt-dlp (no Maton)

This skill uses the **local** `yt-dlp` CLI to query YouTube.

## Requirements
- `yt-dlp` available on PATH

### Install (Windows)
- If you have Python:
  - `python -m pip install -U yt-dlp`
- Or download the Windows binary from the official yt-dlp GitHub releases and put it on PATH.

## Common commands (run on host)
Use `exec` to run these.

### Search
- Top 10 results:
  - `yt-dlp "ytsearch10:<query>" --print "%(title)s\t%(id)s\t%(webpage_url)s" --skip-download`

### Get video details
- `yt-dlp "https://www.youtube.com/watch?v=<id>" --dump-single-json --skip-download`

### Latest uploads from a channel
- `yt-dlp "https://www.youtube.com/@<handle>/videos" --flat-playlist --print "%(title)s\t%(id)s\t%(webpage_url)s" --playlist-end 20`

## Notes / Limits
- This does **not** use YouTube Data API; it scrapes public pages.
- Availability can vary if YouTube changes markup or rate-limits.
- For private account operations (my playlists, comments, etc.), a true OAuth-based API integration is required.
