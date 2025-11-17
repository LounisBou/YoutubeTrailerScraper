# YoutubeTrailerScraper

YoutubeTrailerScraper is a Python package that scans Plex media database folders to find movies and TV shows without trailers. It uses a two-tier approach to find and download trailers:

1. **Primary**: Query TMDB API for official trailer URLs (YouTube links)
2. **Fallback**: If TMDB doesn't have trailers, search directly on YouTube

All trailer videos are downloaded using **yt-dlp**.

## Features

- Scans Plex media directories for content without trailers
- Two-tier trailer discovery strategy (TMDB → YouTube fallback)
- Downloads trailers in Plex-compatible format and structure
- Supports both movies and TV shows
- Configurable via `.env` file

## Architecture

The package is organized around 6 specialized classes:

### Core Components

1. **MovieScanner** (`moviescanner.py`)
   - Scans movie folders for content
   - Detects missing trailers using pattern: `/path/to/movie/movie-trailer.mp4`
   - Returns list of movies without trailers

2. **TVShowScanner** (`tvshowscanner.py`)
   - Scans TV show folders for content
   - Detects missing trailers using pattern: `/path/to/tvshow/trailers/trailer.mp4`
   - Returns list of TV shows without trailers

3. **TMDBSearchEngine** (`tmdbsearchengine.py`)
   - Primary trailer source: Queries TMDB API for official trailers
   - Returns YouTube video URLs from TMDB data
   - Handles movie and TV show searches

4. **YoutubeSearchEngine** (`youtubesearchengine.py`)
   - Fallback method: Direct YouTube searches when TMDB has no trailers
   - Retrieves video information by video ID
   - Returns search results as structured data

5. **YoutubeDownloader** (`youtubedownloader.py`)
   - Downloads YouTube videos using **yt-dlp**
   - Works with URLs from both TMDBSearchEngine and YoutubeSearchEngine
   - Saves videos to appropriate Plex media directories
   - Returns path to downloaded video file

6. **YoutubeTrailerScraper** (`youtubetrailerscraper.py`)
   - Orchestrates the two-tier workflow
   - Loads configuration from `.env` file
   - Manages the complete trailer discovery and download process

## Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/YoutubeTrailerScraper.git
cd YoutubeTrailerScraper

# Install dependencies
pip install -r requirements.txt

# Install package in editable mode
pip install -e .
```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
# TMDB API Configuration
TMDB_API_KEY=your_tmdb_api_key
TMDB_READ_ACCESS_TOKEN=your_tmdb_read_access_token

# Plex Media Directories
MOVIES_DIRS=/path/to/movies1,/path/to/movies2
TVSHOWS_DIRS=/path/to/tvshows1,/path/to/tvshows2

# SMB Mount Point (optional)
SMB_MOUNT_POINT=/Volumes/MediaServer
```

See `.env.example` for a complete configuration template.

### YouTube Authentication (Bypassing Bot Detection)

YouTube may block yt-dlp downloads with bot detection errors. To fix this, configure cookie authentication in your `.env` file:

**Option 1: Use Browser Cookies (Recommended)**

Extract cookies directly from your browser where you're logged into YouTube:

```env
# Supported browsers: firefox, chrome, chromium, edge, opera, brave, safari
YOUTUBE_COOKIES_FROM_BROWSER=firefox
```

**Option 2: Use Cookies File**

Export cookies to a Netscape format file:

1. Install a browser extension to export cookies (e.g., "Get cookies.txt LOCALLY" for Firefox/Chrome)
2. Visit youtube.com while logged in
3. Export cookies to a file
4. Configure the path in `.env`:

```env
YOUTUBE_COOKIES_FILE=/path/to/cookies.txt
```

**Note**: The `YOUTUBE_COOKIES_FROM_BROWSER` option takes precedence if both are configured.

## Usage

```bash
# Run the CLI
python main.py

# With verbose output
python main.py --verbose

# With SMB mount point
python main.py --use-smb
```

## Development Status

**Current Status**: Early development

### Completed ✓
- **Step 0**: Package structure optimization
- **Step 1**: Dependencies (yt-dlp, requests, python-dotenv)
- **Step 2**: Environment variable loading in YoutubeTrailerScraper
- **Pre-Step 3**: Main.py adaptation and pylint cleanup
- **Code quality tools**: `/check-quality` and `/check-docstrings` slash commands

### Next Steps

#### **Step 3: Implement Scanner Classes** (Next priority)
- [ ] **MovieScanner** - Scans movie folders for missing trailers
  - Pattern: `/path/to/movie/movie-trailer.mp4`
  - Returns list of movies without trailers
- [ ] **TVShowScanner** - Scans TV show folders for missing trailers
  - Pattern: `/path/to/tvshow/trailers/trailer.mp4`
  - Returns list of TV shows without trailers

#### **Step 4: Implement Search Engines**
- [ ] **TMDBSearchEngine** - Primary trailer source (TMDB API → YouTube URLs)
- [ ] **YoutubeSearchEngine** - Fallback search (Direct YouTube search)

#### **Step 5: Implement Downloader**
- [ ] **YoutubeDownloader** - Downloads videos using yt-dlp

#### **Step 6: Orchestrate Workflow**
- [ ] Complete the two-tier workflow in YoutubeTrailerScraper:
  - Scan → TMDB search → Fallback to YouTube → Download

## Workflow Strategy

The intended workflow:

1. Scan Plex directories for movies/TV shows without trailers
2. For each media without a trailer:
   - **TMDBSearchEngine**: Query TMDB API for official trailer YouTube URLs
   - If TMDB has trailers → **YoutubeDownloader**: download using yt-dlp
   - If TMDB has no trailers → **YoutubeSearchEngine**: search YouTube directly → **YoutubeDownloader**: download using yt-dlp
3. Save trailers to appropriate Plex directory structure:
   - Movies: `/path/to/movie/movie-trailer.mp4`
   - TV Shows: `/path/to/tvshow/trailers/trailer.mp4`

**Class Responsibilities:**
- **TMDBSearchEngine**: TMDB API → YouTube URLs
- **YoutubeSearchEngine**: Direct YouTube search → YouTube URLs
- **YoutubeDownloader**: YouTube URLs → Downloaded video files

## Development

### Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=youtubetrailerscraper --cov-report=xml
```

### Code Quality

```bash
# Run automated code quality checks
/check-quality

# Format code with black (line length: 99)
black . --line-length=99

# Lint with pylint
pylint src/youtubetrailerscraper/*.py --max-line-length=99

# Check docstrings
/check-docstrings
```

See `CLAUDE.md` for detailed development instructions.

## Fixing Existing Trailers Without .mp4 Extension

If you have previously downloaded trailers that are missing the .mp4 extension due to the bug that was fixed, you can use the `fix_trailer_extensions.py` utility script to rename them:

```bash
# Preview changes (dry-run mode - recommended first step)
python fix_trailer_extensions.py /path/to/movies --dry-run

# Apply changes to a single directory
python fix_trailer_extensions.py /path/to/movies

# Apply changes to multiple directories
python fix_trailer_extensions.py /movies/disk1 /movies/disk2 /movies/disk3

# Verbose output for detailed logging
python fix_trailer_extensions.py /path/to/movies --verbose
```

The script will:
- Scan all movie directories for trailer files
- Identify trailers missing the .mp4 extension
- Rename them to add .mp4 extension
- Skip files that already have .mp4 extension
- Provide a summary of changes made

**Always use `--dry-run` first** to preview the changes before applying them.

## Requirements

- Python 3.9+
- yt-dlp
- requests
- python-dotenv
- [PyMate](https://github.com/lounisbou/PyMate) (pulled automatically via pip; provides the `CacheIt` decorator backed by diskcache and the LogIt logger)

## License

See [LICENSE](LICENSE) file for details.
