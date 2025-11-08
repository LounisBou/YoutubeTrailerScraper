# Development Plan - YoutubeTrailerScraper

This document tracks the development progress of the YoutubeTrailerScraper project.

## Project Overview

YoutubeTrailerScraper is a Python package that scans Plex media database folders to find movies and TV shows without trailers. It uses a two-tier approach:
1. **Primary**: Query TMDB API for official trailer URLs
2. **Fallback**: Search directly on YouTube if TMDB has no trailers

All trailer videos are downloaded using **yt-dlp**.

---

## Development Roadmap

### ✅ Step 0: Package Structure Optimization
**Status**: COMPLETED

**Tasks:**
- [x] Set up src/ layout (`src/youtubetrailerscraper/`)
- [x] Configure package metadata (`setup.py`, `pyproject.toml`)
- [x] Set up testing infrastructure (`pytest`, `conftest.py`)
- [x] Configure code quality tools (black, pylint, mypy, isort)
- [x] Set up GitHub Actions CI/CD

**Files involved:**
- `setup.py`
- `pyproject.toml`
- `tests/conftest.py`
- `.github/workflows/tests.yml`

---

### ✅ Step 1: Dependencies
**Status**: COMPLETED

**Tasks:**
- [x] Add yt-dlp to requirements.txt
- [x] Add requests to requirements.txt
- [x] Add python-dotenv to requirements.txt
- [x] Update package dependencies in setup.py

**Files modified:**
- `requirements.txt`
- `setup.py`

---

### ✅ Step 2: Environment Variable Loading
**Status**: COMPLETED

**Tasks:**
- [x] Create `.env.example` with all required variables
- [x] Implement environment loading in YoutubeTrailerScraper class
- [x] Add validation for required environment variables
- [x] Create tests for environment loading (`tests/test_env_loading.py`)

**Files involved:**
- `.env.example`
- `src/youtubetrailerscraper/youtubetrailerscraper.py`
- `tests/test_env_loading.py`

**Environment Variables:**
- `TMDB_API_KEY` - TMDB API key
- `TMDB_READ_ACCESS_TOKEN` - TMDB read access token
- `MOVIES_DIRS` - Comma-separated movie directory paths
- `TVSHOWS_DIRS` - Comma-separated TV show directory paths
- `SMB_MOUNT_POINT` - Optional SMB mount point

---

### ✅ Pre-Step 3: Main.py Adaptation and Cleanup
**Status**: COMPLETED

**Tasks:**
- [x] Adapt main.py to use YoutubeTrailerScraper class
- [x] Fix all pylint issues across the codebase
- [x] Achieve 10.00/10 pylint score on all files
- [x] Ensure all tests pass

**Files modified:**
- `main.py`
- `commandlinehelper.py`
- All test files

---

### ✅ Code Quality Tools
**Status**: COMPLETED

**Tasks:**
- [x] Create code quality checker agent (`.claude/agents/code-quality-checker.md`)
- [x] Create `/check-quality` slash command
- [x] Create docstring checker agent (`.claude/agents/docstring-checker.md`)
- [x] Create `/check-docstrings` slash command

**Files created:**
- `.claude/agents/code-quality-checker.md`
- `.claude/commands/check-quality.md`
- `.claude/agents/docstring-checker.md`
- `.claude/commands/check-docstrings.md`

---

### 🔄 Step 3: Implement Scanner Classes
**Status**: NOT STARTED

**Priority**: NEXT

**Tasks:**
- [ ] Implement MovieScanner class
  - [ ] Directory scanning logic
  - [ ] Trailer detection (pattern: `/path/to/movie/movie-trailer.mp4`)
  - [ ] Return list of movies without trailers
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests

- [ ] Implement TVShowScanner class
  - [ ] Directory scanning logic
  - [ ] Trailer detection (pattern: `/path/to/tvshow/trailers/trailer.mp4`)
  - [ ] Return list of TV shows without trailers
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests

**Files to modify:**
- `src/youtubetrailerscraper/moviescanner.py`
- `src/youtubetrailerscraper/tvshowscanner.py`
- `tests/test_moviescanner.py` (to be created)
- `tests/test_tvshowscanner.py` (to be created)

**Design considerations:**
- Handle multiple directory paths (from env vars)
- Handle missing directories gracefully
- Support SMB mount points
- Efficient directory traversal
- Error handling for permission issues

---

### 📋 Step 4: Implement Search Engines
**Status**: NOT STARTED

**Tasks:**
- [ ] Implement TMDBSearchEngine class
  - [ ] TMDB API authentication
  - [ ] Movie search endpoint integration
  - [ ] TV show search endpoint integration
  - [ ] Extract YouTube URLs from TMDB video data
  - [ ] Handle API errors and rate limiting
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests (with mocked API responses)

- [ ] Implement YoutubeSearchEngine class
  - [ ] YouTube search functionality
  - [ ] Video ID extraction
  - [ ] Video information retrieval
  - [ ] Search result filtering (prefer official trailers)
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests

**Files to modify:**
- `src/youtubetrailerscraper/tmdbsearchengine.py`
- `src/youtubetrailerscraper/youtubesearchengine.py`
- `tests/test_tmdbsearchengine.py` (to be created)
- `tests/test_youtubesearchengine.py` (to be created)

**API Documentation:**
- TMDB API: https://developers.themoviedb.org/3
- YouTube Data API: https://developers.google.com/youtube/v3

**Design considerations:**
- Rate limiting and retry logic
- Caching API responses (optional)
- Fallback between TMDB and YouTube
- Video quality preferences

---

### 📋 Step 5: Implement Downloader
**Status**: NOT STARTED

**Tasks:**
- [ ] Implement YoutubeDownloader class
  - [ ] yt-dlp integration
  - [ ] Download YouTube videos by URL
  - [ ] Save to appropriate Plex directory structure
  - [ ] Handle download errors and retries
  - [ ] Video format selection (MP4, quality settings)
  - [ ] Progress reporting (optional)
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests

**Files to modify:**
- `src/youtubetrailerscraper/youtubedownloader.py`
- `tests/test_youtubedownloader.py` (to be created)

**yt-dlp options to consider:**
- Format: MP4, H.264 codec
- Quality: 1080p preferred, fallback to lower
- File naming: `movie-trailer.mp4` or `trailer.mp4`
- Download path validation
- Overwrite existing files or skip

**Design considerations:**
- Directory creation (e.g., `tvshow/trailers/`)
- File permissions
- Disk space checking (optional)
- Download resume on failure (yt-dlp handles this)

---

### 📋 Step 6: Orchestrate Workflow
**Status**: NOT STARTED

**Tasks:**
- [ ] Complete YoutubeTrailerScraper workflow implementation
  - [ ] Integrate MovieScanner
  - [ ] Integrate TVShowScanner
  - [ ] Integrate TMDBSearchEngine (primary)
  - [ ] Integrate YoutubeSearchEngine (fallback)
  - [ ] Integrate YoutubeDownloader
  - [ ] Implement two-tier strategy logic
  - [ ] Add progress reporting and logging
  - [ ] Add comprehensive docstrings
  - [ ] Write integration tests

**Files to modify:**
- `src/youtubetrailerscraper/youtubetrailerscraper.py`
- `tests/test_youtubetrailerscraper.py` (update with integration tests)

**Workflow logic:**
```
1. Load environment variables
2. Scan movies (MovieScanner) → List[Movie without trailers]
3. Scan TV shows (TVShowScanner) → List[TVShow without trailers]
4. For each movie/show:
   a. Try TMDBSearchEngine.search(title, year)
   b. If TMDB returns YouTube URLs:
      - YoutubeDownloader.download(url, destination)
   c. Else (TMDB has no trailers):
      - YoutubeSearchEngine.search(title, year)
      - YoutubeDownloader.download(url, destination)
5. Report success/failure statistics
```

**Design considerations:**
- Batch processing vs one-at-a-time
- Error handling (continue on failure vs stop)
- Dry-run mode (scan only, no download)
- Logging levels (INFO, DEBUG, WARNING, ERROR)

---

## Future Enhancements (Post v1.0)

### Potential Features:
- [ ] Web UI for monitoring progress
- [ ] Database to track processed media
- [ ] Configurable download quality preferences
- [ ] Support for other video platforms (Vimeo, Dailymotion)
- [ ] Automatic scheduling (cron job integration)
- [ ] Notification system (email, Slack, Discord)
- [ ] Multi-language trailer support
- [ ] Trailer selection by duration preference
- [ ] Docker container support
- [ ] Plex API integration (direct library updates)

---

## Testing Strategy

### Unit Tests
- Test each class in isolation
- Mock external dependencies (API calls, file system)
- Achieve >80% code coverage

### Integration Tests
- Test workflow end-to-end with test fixtures
- Use sample directory structures
- Mock API responses but test real file operations

### CI/CD
- Run tests on Python 3.9, 3.10, 3.11, 3.12
- Run pylint, black, mypy, isort checks
- Generate coverage reports

---

## Notes

### Current Blockers:
- None

### Decisions Made:
1. **Two-tier approach**: TMDB primary, YouTube fallback (better quality trailers from TMDB)
2. **Google-style docstrings**: Consistent documentation format
3. **src/ layout**: Modern Python package structure
4. **yt-dlp over youtube-dl**: More actively maintained

### Open Questions:
- Should we support trailer selection by user (multiple results)?
- Should we implement caching of API responses?
- What should happen if download fails after multiple retries?
- Should we support custom trailer naming conventions?

---

**Last Updated**: 2025-11-08
