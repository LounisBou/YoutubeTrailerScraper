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

### ✅ Step 3: Implement Scanner Classes
**Status**: COMPLETED

**Tasks:**
- [x] Create FileSystemScanner service class (dependency injection pattern)
  - [x] Generic filesystem scanning with caching (24-hour TTL)
  - [x] Video file detection utilities
  - [x] Path validation and error handling
  - [x] Comprehensive docstrings (Google-style)
  - [x] Unit tests (30 tests covering all functionality)

- [x] Refactor MovieScanner class to use FileSystemScanner
  - [x] Directory scanning logic (delegates to FileSystemScanner)
  - [x] Trailer detection (pattern: `/path/to/movie/movie-trailer.mp4`)
  - [x] Return list of movies without trailers
  - [x] Dependency injection support
  - [x] Add comprehensive docstrings
  - [x] Unit tests already existed (14 tests, all passing)

- [x] Implement TVShowScanner class using FileSystemScanner
  - [x] Directory scanning logic (delegates to FileSystemScanner)
  - [x] Trailer detection (pattern: `/path/to/tvshow/trailers/trailer.mp4`)
  - [x] Return list of TV shows without trailers
  - [x] Configurable season directory pattern (via `season_pattern` parameter)
  - [x] Season directory detection (case-insensitive)
  - [x] Dependency injection support
  - [x] Add comprehensive docstrings
  - [x] Write unit tests (21 tests covering all functionality including custom patterns)

**Files created/modified:**
- ✅ `src/youtubetrailerscraper/filesystemscanner.py` (NEW - 214 lines)
- ✅ `src/youtubetrailerscraper/moviescanner.py` (REFACTORED - reduced from 206 to 144 lines)
- ✅ `src/youtubetrailerscraper/tvshowscanner.py` (IMPLEMENTED - 194 lines with configurable season pattern)
- ✅ `tests/test_filesystemscanner.py` (NEW - 30 tests)
- ✅ `tests/test_tvshowscanner.py` (NEW - 21 tests including custom pattern tests)
- ✅ `tests/test_moviescanner.py` (existing - 14 tests, all passing)
- ✅ `.env.example` (UPDATED - includes `TVSHOWS_SEASON_SUBDIR_PATTERN` variable)

**Design patterns used:**
- **Dependency Injection**: FileSystemScanner injected into scanner classes
- **Service Layer Pattern**: FileSystemScanner as shared service
- **Strategy Pattern**: Different trailer detection strategies per media type
- **DRY Principle**: Eliminated ~60% code duplication

**Benefits achieved:**
- Single source of truth for filesystem operations
- Easy to test with mocked FileSystemScanner
- Consistent caching behavior across scanners
- Reduced code duplication significantly
- Better separation of concerns

**Test coverage:**
- Total: 65 tests (all passing)
- FileSystemScanner: 30 tests
- MovieScanner: 14 tests
- TVShowScanner: 21 tests (includes custom season pattern tests)

**Code quality:**
- Black: ✅ All files formatted (99 char line length)
- isort: ✅ All imports sorted
- mypy: ✅ No type errors
- pylint: ✅ 10.00/10 across all files

---

### ✅ Step 4a: Implement TMDB Search Engine + Full Integration
**Status**: FULLY COMPLETED (with multi-language support)

**Part 1: TMDBSearchEngine Class**
- [x] Implement TMDBSearchEngine class
  - [x] TMDB API authentication via API key
  - [x] Movie search endpoint integration (`/search/movie`, `/movie/{id}/videos`)
  - [x] TV show search endpoint integration (`/search/tv`, `/tv/{id}/videos`)
  - [x] Extract YouTube URLs from TMDB video data (filters for type="Trailer" and site="YouTube")
  - [x] Handle API errors and rate limiting (retry logic with configurable attempts and delays)
  - [x] **Multi-language fallback search** (configurable languages, tries each until results found)
  - [x] Add comprehensive docstrings (Google-style with examples)
  - [x] Write unit tests (30 comprehensive tests with mocked API responses)

**Part 2: YoutubeTrailerScraper Integration**
- [x] Add TMDBSearchEngine instance to YoutubeTrailerScraper
- [x] Implement metadata extraction utilities
  - [x] `_extract_movie_metadata(path)`: Extract title and year from directory names
  - [x] `_extract_tvshow_metadata(path)`: Extract TV show title and year
- [x] Implement search methods
  - [x] `search_for_movie_trailer(title, year)`: Search TMDB for movie trailers
  - [x] `search_for_tvshow_trailer(title, year)`: Search TMDB for TV show trailers
- [x] Implement orchestration methods
  - [x] `search_trailers_for_movies(paths)`: Batch search for multiple movies
  - [x] `search_trailers_for_tvshows(paths)`: Batch search for multiple TV shows

**Part 3: CLI Integration**
- [x] Add `--search-tmdb` flag to commandlinehelper.py
- [x] Implement `_search_and_display_tmdb_results()` in main.py
- [x] Create helper functions for cleaner code:
  - [x] `_display_media_search_results()`: Display search results
  - [x] `_search_movies_on_tmdb()`: Search movies and display results
  - [x] `_search_tvshows_on_tmdb()`: Search TV shows and display results
- [x] Integrate TMDB search into main workflow

**Part 4: Integration Tests**
- [x] Create comprehensive integration test suite (`tests/test_tmdb_integration.py`)
- [x] Metadata extraction tests (7 tests)
- [x] Search integration tests (6 tests)
- [x] Orchestration tests (6 tests)
- [x] End-to-end workflow tests (2 tests)
- [x] Update existing test for `search_for_movie_trailer` with mocks

**Files created/modified:**
- ✅ `src/youtubetrailerscraper/tmdbsearchengine.py` (216 lines)
- ✅ `src/youtubetrailerscraper/youtubetrailerscraper.py` (+150 lines of integration code)
- ✅ `tests/test_tmdbsearchengine.py` (365 lines - 30 tests)
- ✅ `tests/test_tmdb_integration.py` (382 lines - 21 tests, NEW)
- ✅ `tests/test_youtubetrailerscraper.py` (updated 1 test with mock)
- ✅ `main.py` (+120 lines for TMDB search display)
- ✅ `commandlinehelper.py` (+6 lines for --search-tmdb flag)

**Total test coverage:**
- TMDBSearchEngine: 30 tests (all passing)
- TMDB Integration: 21 tests (all passing)
- Updated tests: 1 test
- **Total: 168 tests passing, 99% code coverage**

**Implementation highlights:**
- **Metadata extraction**: Regex-based parsing of directory names to extract title and year
- **Batch processing**: Orchestration methods efficiently process multiple movies/TV shows
- **Multi-language search**: Automatically tries multiple TMDB language settings (fr-FR, en-US, etc.) in order
- **Comprehensive logging**: Debug, info, and success messages throughout the workflow
- **CLI demonstration**: Full integration test via `python main.py` command (automatic TMDB search)
- **Error handling**: Graceful handling of API failures, missing data, and empty results

**Code quality (all files):**
- Black: ✅ All files formatted (99 char line length)
- isort: ✅ All imports sorted
- mypy: ✅ No type errors
- pylint: ✅ 10.00/10 score across all files
- Coverage: ✅ 99% (1 unreachable line is acceptable)

**Multi-language configuration:**
Add `TMDB_LANGUAGES` to your `.env` file to specify language priority order:
```bash
# Try French first, then English
TMDB_LANGUAGES=["fr-FR", "en-US"]

# Try English only (default)
TMDB_LANGUAGES=["en-US"]

# Try German, then French, then English
TMDB_LANGUAGES=["de-DE", "fr-FR", "en-US"]
```

**Usage example:**
```bash
# Scan for missing trailers and automatically search TMDB
python main.py

# With verbose output showing full URLs
python main.py --verbose

# Sample mode (automatically searches TMDB for results)
python main.py --scan-sample
```

**Note**:
- TMDB search happens automatically for all movies/TV shows without trailers. No flag required!
- Multi-language fallback tries each configured language until trailers are found
- Plex folders can have titles in any language (French, English, German, etc.)

---

### 📋 Step 4b: Implement YouTube Search Engine (Fallback)
**Status**: NOT STARTED

**Tasks:**
- [ ] Implement YoutubeSearchEngine class
  - [ ] YouTube search functionality
  - [ ] Video ID extraction
  - [ ] Video information retrieval
  - [ ] Search result filtering (prefer official trailers)
  - [ ] Add comprehensive docstrings
  - [ ] Write unit tests

**Files to modify:**
- `src/youtubetrailerscraper/youtubesearchengine.py`
- `tests/test_youtubesearchengine.py` (to be created)

**API Documentation:**
- YouTube Data API: https://developers.google.com/youtube/v3

**Design considerations:**
- This will be the fallback when TMDB has no trailers
- Should use web scraping or YouTube Data API (requires API key)
- Consider using yt-dlp search capabilities as alternative

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

### 📋 Step 7: Code Reorganization
**Status**: NOT STARTED

**Tasks:**
- [ ] Reorganize `src/youtubetrailerscraper/` into logical subfolders
  - [ ] Create `scanners/` subfolder (filesystemscanner.py, moviescanner.py, tvshowscanner.py)
  - [ ] Create `search/` subfolder (tmdbsearchengine.py, youtubesearchengine.py)
  - [ ] Create `download/` subfolder (youtubedownloader.py)
  - [ ] Keep `youtubetrailerscraper.py` at top level (main orchestrator)
  - [ ] Update all imports across the codebase
  - [ ] Add `__init__.py` files to each subfolder
  - [ ] Update test imports
  - [ ] Verify all tests still pass

**Files to modify:**
- All files in `src/youtubetrailerscraper/`
- All test files in `tests/`
- `main.py` (import statements)
- Package `__init__.py`

**Proposed structure:**
```
src/youtubetrailerscraper/
├── __init__.py
├── _about.py
├── scanners/
│   ├── __init__.py
│   ├── filesystemscanner.py
│   ├── moviescanner.py
│   └── tvshowscanner.py
├── search/
│   ├── __init__.py
│   ├── tmdbsearchengine.py
│   └── youtubesearchengine.py
├── download/
│   ├── __init__.py
│   └── youtubedownloader.py
└── youtubetrailerscraper.py
```

**Rationale:**
- Clear separation of concerns (scan → search → download)
- Better scalability for future additions
- Mirrors the 3-tier architecture workflow
- Easier to maintain and navigate as codebase grows

**Note:** This step should be done AFTER Steps 4-6 are complete to avoid unnecessary churn during active development.

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

## Engineering Improvement Ideas

1. **Document PyMate as a core dependency**  
   - Add `pymate` (and the `diskcache` backend it relies on) to `pyproject.toml`/`requirements.txt` with pinned versions.  
   - Call out the dependency explicitly in `README.md` and `.env.example` so downstream consumers know they must install it before running the CLI.

2. **Add a `--env-file` CLI switch**  
   - Let users point the CLI at any configuration file (e.g., `python main.py --env-file ~/configs/prod.env`) without copying it to the repo root.  
   - Thread the selected path into `YoutubeTrailerScraper` so tests can drop per-suite configs without mucking with `.env`.

3. **Align docs with actual env variable names**  
   - Update `README.md` and `.env.example` to refer to `MOVIES_PATHS`/`TVSHOWS_PATHS` (Python list syntax) instead of the legacy `*_DIRS` comma-separated strings.  
   - Add a short rationale plus examples for SMB prefixing to reduce onboarding friction.

4. **Improve CLI ergonomics**  
   - Provide a `--dry-run` flag that only reports missing trailers (no future downloads/searches) and a `--json` output mode for piping results into automation.  
   - Share the single `LogIt` instance across helpers (already started) and surface a `--log-file` argument for long-running scans.

5. **Configuration validation & health checks**  
   - During startup, add optional checks that the TMDB token and YouTube connectivity work (fail fast with actionable errors).  
   - Extend `commandlinehelper.check_args` to validate SMB mount availability when `--use-smb` is passed and to warn when configured paths do not exist.

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

**Last Updated**: 2025-11-10 (Step 4a fully completed - TMDB search is now automatic with multi-language support)
