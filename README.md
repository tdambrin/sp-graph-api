# Spotify - Deprecated

Spotify deprecated most endpoints on 27 November 2024. Check out [their post](https://developer.spotify.com/blog/2024-11-27-changes-to-the-web-api)

# New: Deezer Graph Search

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)


<p align="center">
  <a href="https://spotify-graph-api-4b00479b17ee.herokuapp.com/docs#/" target="_blank">
    <img src="https://github.com/tandpfun/skill-icons/blob/main/icons/FastAPI.svg" style="width:50px;height:50px;">
  </a>
</p>

##  Dev

To run locally, simply do

```bash
$ make install
$ make run-local
```

## Version 0.1 - Build graph from query :white_check_mark:

- [x] Depth 2 graph from query node including all types
- [x] Recommendations are tracks only
- [x] Graph viz ugly but functional

## Version 0.2 - Improve viz and interactions
- [x] Different colors for different types
- [x] Description on hover
- [x] Preview picture
- [x] Redirect spotify on alt click
- [x] Space out nodes - Atlas model
- [x] Play track preview on hover

# Version 0.3 - Improve recommendations and UX
- [x] The search endpoint can restrict types to be subsets of track, album, artist
- [x] Incremental refresh of the graph when search
- [x] Query 1 level from any node you click
- [x] Fix player bug that keeps running when leaving node

# Version 0.4 - Make it smooth
- [x] Refactor in API vs Streamlit (Remove streamlit API wrapper, use fastapi)
- [x] Create tasks from Graph JS by calling API and fetch until completed/failed
- [x] Restore search incremental display
- [x] Open spotify -> switch to shift click
- [x] Delete node on alt click
- [x] Interactive graph - not just player, update when (un)select types, load progressively

# Version 0.4.1 - Refactor API
- [x] Remove UI components
- [x] Make API multi user with sessions
- [x] Fix node retrieval when not in memory for all types

# Version 0.5 - UX
- [x] Artists connect to artists
- [x] A track is only connected to an album or artist it is part of
- [ ] Search by popularity
  - either automatically get diverse popularity scores (i.e. if taylor then not ariana)
  - or set popularity thresholds
- [ ] Export to playlist
- [ ] Match with user's knowledge
  - flag new vs known
- [x] Transparent edges on stars
- [x] Fix backbone transparent from track -> done in frontend
- [x] Random color for star groups
- [x] Node size linear to popularity
- [x] Prune graph with depth on delete

# Version 0.6 - Enable graph ops
- [ ] Add visual directions to edges and semantic labels to edges (TRACK_OF, SIMILAR_TO, ALBUM_OF, AUTHOR_OF)

# Version 0.7 - Switched to Deezer
