# Glomatico's YouTube Music Downloader (Concurrent Download)

A fork of gytmdl with concurrent download

## Setup
1. Use as python module
   ```
   python -m gytmdl "YOUR_PLAYLIST_URL"
   ```
## Usage examples
The default number of concurrent downloads is 3. Use argument --num_workers / -w

Download a song:
```
python -m gytmdl "https://music.youtube.com/watch?v=3BFTio5296w" 
```
Download an album:
```
python -m gytmdl "YOUR_PLAYLIST_URL" --num_workers 10
```
Download from multiple album:
```
python -m gytmdl "YOUR_PLAYLIST_URL1" "YOUR_PLAYLIST_URL2" -w 10
```
Download from URL lists:
```
python -m gytmdl -u "YOUR_URSLS_TXT" -w 10
```
## Configurations
For detailed configurations, please visit the original repo at https://github.com/glomatico/gytmdl
