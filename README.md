# Glomatico's YouTube Music Downloader (Multithreaded Download)

A fork of gytmdl, supercharged with multithreaded download!
Download YouTube Music songs/albums/playlists with tags from YouTube Music in 256kbps AAC/128kbps Opus/128kbps AAC.

## Setup
1. Install python build
   ```
   pip install build
   ```
2. Build the cli tool
   ```
   python -m build
   ```
   OR
3. Use as python module
   ```
   python -m gytmdl "YOUR_PLAYLIST_URL"
   ```
## Usage examples
Download a song:
```
gytmdl "https://music.youtube.com/watch?v=3BFTio5296w"
```
Download an album:
```
gytmdl "YOUR_PLAYLIST_URL"
```
Download from multiple album:
```
gytmdl "YOUR_PLAYLIST_URL1" "YOUR_PLAYLIST_URL2"
```
## Configurations
For detailed configurations, please visit the original repo at https://github.com/glomatico/gytmdl
