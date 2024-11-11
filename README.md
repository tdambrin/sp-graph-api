# Spotify Graph Search

![Python](https://img.shields.io/badge/python-3.10%20%7C%203.11%20%7C%203.12-blue)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Imports: isort](https://img.shields.io/badge/%20imports-isort-%231674b1?style=flat&labelColor=ef8336)](https://pycqa.github.io/isort/)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://mypy-lang.org/)
[![Pydantic v2](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/pydantic/pydantic/main/docs/badge/v2.json)](https://pydantic.dev)
[![pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?logo=pre-commit&logoColor=white)](https://github.com/pre-commit/pre-commit)

## Dev

To run locally, simply do

```bash
$ make install
$ make run
```

## Version 0.1 - Build graph from query :white_check_mark:

- Depth 2 graph from query node including all types
- Recommendations are tracks only
- Graph viz ugly but functional

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
- [ ] Make API multi user with sessions
- [ ] Interactive graph - not just player, update when (un)select types, load progressively
